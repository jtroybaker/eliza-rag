from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from time import sleep
import re
from typing import Callable, Literal

import lancedb

from .config import Settings
from .corpus import inspect_corpus
from .embeddings import (
    encode_text,
    expand_query_terms,
    load_dense_index_metadata,
    resolve_embedder,
    warm_embedder_model,
)
from .interfaces import QueryAnalyzer, Reranker, Retriever
from .models import RetrievalFilters, RetrievalRerankConfig, RetrievalResult, StructuredQuery
from .storage import prepare_lancedb_artifacts

RetrievalMode = Literal["lexical", "dense", "hybrid", "targeted_hybrid"]

LEXICAL_RETRIEVAL_MODE = "lexical"
DENSE_RETRIEVAL_MODE = "dense"
HYBRID_RETRIEVAL_MODE = "hybrid_rrf"
TARGETED_HYBRID_RETRIEVAL_MODE = "targeted_hybrid_rrf"
HEURISTIC_RERANKER = "heuristic"
BGE_RERANKER_V2_M3 = "bge-reranker-v2-m3"
BGE_RERANKER_BASE = "bge-reranker-base"
_BGE_RERANKER_REPO_ID = "BAAI/bge-reranker-v2-m3"
_BGE_RERANKER_BASE_REPO_ID = "BAAI/bge-reranker-base"
TEXT_INDEX_NAME = "text_idx"
VECTOR_INDEX_NAME = "vector_idx"
FILTER_INDEX_COLUMNS = ("ticker", "form_type", "filing_date")
_PHRASE_READY_TABLES: set[tuple[str, str]] = set()
_YEAR_RE = re.compile(r"\b(20\d{2})\b")
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_COMPARISON_PHRASES = (
    "compare",
    "comparison",
    "how do they compare",
    "versus",
    " vs ",
    "relative to",
    "contrast",
    "different from",
    "differences between",
    "similarities between",
    "both",
    "between ",
)
_CORPORATE_SUFFIXES = frozenset(
    {
        "inc",
        "incorporated",
        "corp",
        "corporation",
        "company",
        "co",
        "holdings",
        "holding",
        "group",
        "plc",
        "ltd",
        "limited",
        "llc",
        "sa",
        "ag",
        "nv",
        "the",
    }
)
_ALIAS_STOPWORDS = frozenset({"and", "of"})
_GENERIC_SINGLE_TOKEN_ALIASES = frozenset(
    {
        "bank",
        "financial",
        "group",
        "holding",
        "holdings",
        "company",
        "corporation",
        "corp",
        "inc",
        "co",
    }
)


@dataclass(frozen=True, slots=True)
class CompanyCatalogEntry:
    ticker: str
    company_name: str | None
    aliases: tuple[str, ...]


class DenseIndexNotReadyError(RuntimeError):
    """Raised when dense or hybrid retrieval is requested before dense artifacts exist."""


class LexicalIndexNotReadyError(RuntimeError):
    """Raised when lexical retrieval is requested before lexical artifacts exist."""


class DeterministicQueryAnalyzer:
    def analyze(
        self,
        query: str,
        *,
        filters: RetrievalFilters | None = None,
        settings: Settings | None = None,
    ) -> StructuredQuery:
        expansion_terms = expand_query_terms(query)
        years = sorted({match.group(1) for match in _YEAR_RE.finditer(query)})
        filing_date_from = filters.filing_date_from if filters else None
        filing_date_to = filters.filing_date_to if filters else None
        detected_tickers, detected_company_names = detect_query_companies(query, settings=settings)
        target_tickers = _combine_unique(filters.tickers if filters else None, detected_tickers)
        is_multi_company = len(target_tickers) >= 2
        is_comparison_query = detect_comparison_intent(query)

        if not filing_date_from and years:
            filing_date_from = f"{years[0]}-01-01"
        if not filing_date_to and years:
            filing_date_to = f"{years[-1]}-12-31"

        lexical_query = query
        dense_query = query
        if expansion_terms:
            dense_query = f"{query} {' '.join(expansion_terms)}"

        return StructuredQuery(
            raw_query=query,
            retrieval_text=query,
            lexical_query=lexical_query,
            dense_query=dense_query,
            expansion_terms=expansion_terms,
            normalized_tickers=filters.tickers if filters else None,
            detected_tickers=detected_tickers or None,
            detected_company_names=detected_company_names or None,
            target_tickers=target_tickers or None,
            filing_date_from=filing_date_from,
            filing_date_to=filing_date_to,
            is_multi_company=is_multi_company,
            is_comparison_query=is_comparison_query,
            requires_entity_coverage=is_multi_company and (is_comparison_query or bool(detected_company_names)),
        )


class LexicalRetrieverAdapter:
    mode = "lexical"

    def retrieve(
        self,
        settings: Settings,
        structured_query: StructuredQuery,
        *,
        top_k: int | None = None,
        filters: RetrievalFilters | None = None,
        phrase_query: bool = False,
    ) -> list[RetrievalResult]:
        return retrieve_lexical(
            settings,
            structured_query.lexical_query,
            top_k=top_k,
            filters=filters,
            phrase_query=phrase_query,
        )


class DenseRetrieverAdapter:
    mode = "dense"

    def retrieve(
        self,
        settings: Settings,
        structured_query: StructuredQuery,
        *,
        top_k: int | None = None,
        filters: RetrievalFilters | None = None,
        phrase_query: bool = False,
    ) -> list[RetrievalResult]:
        return retrieve_dense(
            settings,
            structured_query.dense_query,
            top_k=top_k,
            filters=filters,
        )


class HybridRetrieverAdapter:
    mode = "hybrid"

    def retrieve(
        self,
        settings: Settings,
        structured_query: StructuredQuery,
        *,
        top_k: int | None = None,
        filters: RetrievalFilters | None = None,
        phrase_query: bool = False,
    ) -> list[RetrievalResult]:
        return retrieve_hybrid(
            settings,
            structured_query=structured_query,
            top_k=top_k,
            filters=filters,
            phrase_query=phrase_query,
        )


class TargetedHybridRetrieverAdapter:
    mode = "targeted_hybrid"

    def retrieve(
        self,
        settings: Settings,
        structured_query: StructuredQuery,
        *,
        top_k: int | None = None,
        filters: RetrievalFilters | None = None,
        phrase_query: bool = False,
    ) -> list[RetrievalResult]:
        return retrieve_targeted_hybrid(
            settings,
            structured_query=structured_query,
            top_k=top_k,
            filters=filters,
            phrase_query=phrase_query,
        )


class HeuristicRerankerAdapter:
    name = HEURISTIC_RERANKER

    def score(
        self,
        structured_query: StructuredQuery,
        results: list[RetrievalResult],
    ) -> list[float]:
        query_terms = _tokenize(_build_rerank_query_text(structured_query))
        query_text = structured_query.raw_query.strip().lower()
        return [
            _score_result_for_rerank(
                result,
                query_terms=query_terms,
                query_text=query_text,
            )
            for result in results
        ]


class BGERerankerAdapter:
    name = BGE_RERANKER_V2_M3

    def score(
        self,
        structured_query: StructuredQuery,
        results: list[RetrievalResult],
    ) -> list[float]:
        return _score_with_transformer_reranker(
            structured_query.raw_query,
            results,
            repo_id=_BGE_RERANKER_REPO_ID,
        )


class BGEBaseRerankerAdapter:
    name = BGE_RERANKER_BASE

    def score(
        self,
        structured_query: StructuredQuery,
        results: list[RetrievalResult],
    ) -> list[float]:
        return _score_with_transformer_reranker(
            structured_query.raw_query,
            results,
            repo_id=_BGE_RERANKER_BASE_REPO_ID,
        )


def open_chunk_table(settings: Settings) -> lancedb.table.Table:
    database = lancedb.connect(settings.lancedb_dir)
    return database.open_table(settings.lancedb_table_name)


def open_dense_chunk_table(settings: Settings) -> lancedb.table.Table:
    database = lancedb.connect(settings.lancedb_dir)
    return database.open_table(settings.dense_lancedb_table_name)


def analyze_query(
    query: str,
    *,
    filters: RetrievalFilters | None = None,
    settings: Settings | None = None,
) -> StructuredQuery:
    return build_query_analyzer().analyze(query, filters=filters, settings=settings)


def merge_query_filters(structured_query: StructuredQuery, filters: RetrievalFilters | None) -> RetrievalFilters | None:
    merged = RetrievalFilters(
        tickers=filters.tickers if filters else structured_query.normalized_tickers,
        form_types=filters.form_types if filters else None,
        filing_date_from=filters.filing_date_from if filters and filters.filing_date_from else structured_query.filing_date_from,
        filing_date_to=filters.filing_date_to if filters and filters.filing_date_to else structured_query.filing_date_to,
    )
    if merged.to_dict() == RetrievalFilters().to_dict():
        return None
    return merged


def ensure_lexical_indices(
    settings: Settings,
    *,
    require_phrase_support: bool = False,
) -> dict[str, object]:
    table = open_chunk_table(settings)
    table_key = (str(settings.lancedb_dir), settings.lancedb_table_name)
    existing_indices = {index.name for index in table.list_indices()}

    if TEXT_INDEX_NAME not in existing_indices or (
        require_phrase_support and table_key not in _PHRASE_READY_TABLES
    ):
        _retry_index_update(
            lambda: table.create_fts_index(
                "text",
                replace=TEXT_INDEX_NAME in existing_indices,
                with_position=require_phrase_support,
            )
        )
        existing_indices = {index.name for index in table.list_indices()}
        if require_phrase_support:
            _PHRASE_READY_TABLES.add(table_key)

    for column in FILTER_INDEX_COLUMNS:
        if f"{column}_idx" not in existing_indices:
            _retry_index_update(lambda column=column: table.create_scalar_index(column, replace=False))
            existing_indices = {index.name for index in table.list_indices()}

    return {
        "table_name": settings.lancedb_table_name,
        "index_names": sorted(existing_indices),
    }


def ensure_dense_indices(settings: Settings) -> dict[str, object]:
    table = open_dense_chunk_table(settings)
    existing_indices = {index.name for index in table.list_indices()}

    if VECTOR_INDEX_NAME not in existing_indices:
        _retry_index_update(
            lambda: table.create_index(
                metric=settings.dense_index_metric,
                vector_column_name="vector",
                replace=True,
                index_type="IVF_HNSW_PQ",
                name=VECTOR_INDEX_NAME,
            )
        )
        existing_indices = {index.name for index in table.list_indices()}

    for column in FILTER_INDEX_COLUMNS:
        if f"{column}_idx" not in existing_indices:
            _retry_index_update(lambda column=column: table.create_scalar_index(column, replace=False))
            existing_indices = {index.name for index in table.list_indices()}

    return {
        "table_name": settings.dense_lancedb_table_name,
        "index_names": sorted(existing_indices),
    }


def index_status(settings: Settings) -> dict[str, object]:
    status: dict[str, object] = {
        "lexical": _artifact_status(settings, dense=False),
        "dense": _artifact_status(settings, dense=True),
    }
    return status


def build_filter_sql(filters: RetrievalFilters | None) -> str | None:
    if filters is None:
        return None

    clauses: list[str] = []
    if filters.tickers:
        clauses.append(_in_clause("ticker", filters.tickers))
    if filters.form_types:
        clauses.append(_in_clause("form_type", filters.form_types))
    if filters.filing_date_from:
        clauses.append(f"filing_date >= '{_escape_sql_string(filters.filing_date_from)}'")
    if filters.filing_date_to:
        clauses.append(f"filing_date <= '{_escape_sql_string(filters.filing_date_to)}'")

    return " AND ".join(clauses) or None


def retrieve(
    settings: Settings,
    query: str,
    *,
    mode: RetrievalMode = "lexical",
    top_k: int | None = None,
    filters: RetrievalFilters | None = None,
    phrase_query: bool = False,
    enable_rerank: bool | None = None,
    reranker: str | None = None,
    rerank_candidate_pool: int | None = None,
) -> list[RetrievalResult]:
    structured_query = build_query_analyzer().analyze(query, filters=filters, settings=settings)
    merged_filters = merge_query_filters(structured_query, filters)
    limit = top_k or settings.retrieval_top_k
    rerank_config = resolve_rerank_config(
        settings,
        top_k=limit,
        enable_rerank=enable_rerank,
        reranker=reranker,
        rerank_candidate_pool=rerank_candidate_pool,
    )
    candidate_limit = rerank_config.candidate_pool if rerank_config else limit
    results = build_retriever(mode).retrieve(
        settings,
        structured_query,
        top_k=candidate_limit,
        filters=merged_filters,
        phrase_query=phrase_query,
    )
    return rerank_results(structured_query, results, top_k=limit, rerank_config=rerank_config)


def retrieve_lexical(
    settings: Settings,
    query: str,
    *,
    top_k: int | None = None,
    filters: RetrievalFilters | None = None,
    phrase_query: bool = False,
) -> list[RetrievalResult]:
    ensure_lexical_retrieval_ready(settings)
    ensure_lexical_indices(settings, require_phrase_support=phrase_query)
    table = open_chunk_table(settings)
    limit = top_k or settings.retrieval_top_k

    search = table.search(query, query_type="fts", fts_columns="text")
    if phrase_query:
        search = search.phrase_query()

    filter_sql = build_filter_sql(filters)
    if filter_sql:
        search = search.where(filter_sql, prefilter=True)

    rows = search.limit(limit).to_list()
    return [_normalize_result(row, rank=rank, retrieval_mode=LEXICAL_RETRIEVAL_MODE) for rank, row in enumerate(rows, start=1)]


def retrieve_dense(
    settings: Settings,
    query: str,
    *,
    top_k: int | None = None,
    filters: RetrievalFilters | None = None,
) -> list[RetrievalResult]:
    ensure_dense_retrieval_ready(settings)
    ensure_dense_indices(settings)
    table = open_dense_chunk_table(settings)
    metadata = load_dense_index_metadata(settings)
    query_vector = encode_text(query, metadata)
    limit = top_k or settings.retrieval_top_k

    search = table.search(query_vector, vector_column_name="vector").metric(settings.dense_index_metric)
    filter_sql = build_filter_sql(filters)
    if filter_sql:
        search = search.where(filter_sql, prefilter=True)

    rows = search.limit(limit).to_list()
    return [_normalize_result(row, rank=rank, retrieval_mode=DENSE_RETRIEVAL_MODE) for rank, row in enumerate(rows, start=1)]


def retrieve_hybrid(
    settings: Settings,
    *,
    structured_query: StructuredQuery,
    top_k: int | None = None,
    filters: RetrievalFilters | None = None,
    phrase_query: bool = False,
) -> list[RetrievalResult]:
    limit = top_k or settings.retrieval_top_k
    lexical_results = retrieve_lexical(
        settings,
        structured_query.lexical_query,
        top_k=max(limit * 2, limit),
        filters=filters,
        phrase_query=phrase_query,
    )
    dense_results = retrieve_dense(
        settings,
        structured_query.dense_query,
        top_k=max(limit * 2, limit),
        filters=filters,
    )

    fused_scores: dict[str, float] = {}
    fused_results: dict[str, RetrievalResult] = {}
    for results in (lexical_results, dense_results):
        for result in results:
            fused_scores[result.chunk_id] = fused_scores.get(result.chunk_id, 0.0) + (1.0 / (60 + result.rank))
            fused_results.setdefault(result.chunk_id, result)

    ranked = sorted(
        fused_results.values(),
        key=lambda result: (-fused_scores[result.chunk_id], result.chunk_id),
    )[:limit]
    return [
        replace(result, rank=rank, raw_score=fused_scores[result.chunk_id], retrieval_mode=HYBRID_RETRIEVAL_MODE)
        for rank, result in enumerate(ranked, start=1)
    ]


def retrieve_targeted_hybrid(
    settings: Settings,
    *,
    structured_query: StructuredQuery,
    top_k: int | None = None,
    filters: RetrievalFilters | None = None,
    phrase_query: bool = False,
) -> list[RetrievalResult]:
    limit = top_k or settings.retrieval_top_k
    target_tickers = structured_query.target_tickers or []
    if not structured_query.requires_entity_coverage or len(target_tickers) < 2:
        return [
            replace(result, retrieval_mode=TARGETED_HYBRID_RETRIEVAL_MODE)
            for result in retrieve_hybrid(
                settings,
                structured_query=structured_query,
                top_k=limit,
                filters=filters,
                phrase_query=phrase_query,
            )
        ]

    per_ticker_limit = max(1, limit // len(target_tickers))
    ticker_results: list[list[RetrievalResult]] = []
    seen_chunk_ids: set[str] = set()
    ordered_results: list[RetrievalResult] = []

    for ticker in target_tickers:
        scoped_filters = _with_ticker_filter(filters, ticker)
        results = retrieve_hybrid(
            settings,
            structured_query=structured_query,
            top_k=max(per_ticker_limit, 1),
            filters=scoped_filters,
            phrase_query=phrase_query,
        )
        ticker_results.append(results)

    for position in range(max((len(results) for results in ticker_results), default=0)):
        for results in ticker_results:
            if position >= len(results):
                continue
            result = results[position]
            if result.chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(result.chunk_id)
            ordered_results.append(replace(result, retrieval_mode=TARGETED_HYBRID_RETRIEVAL_MODE))
            if len(ordered_results) >= limit:
                return ordered_results

    fallback_results = retrieve_hybrid(
        settings,
        structured_query=structured_query,
        top_k=limit,
        filters=filters,
        phrase_query=phrase_query,
    )
    for result in fallback_results:
        if result.chunk_id in seen_chunk_ids:
            continue
        seen_chunk_ids.add(result.chunk_id)
        ordered_results.append(replace(result, retrieval_mode=TARGETED_HYBRID_RETRIEVAL_MODE))
        if len(ordered_results) >= limit:
            break
    return ordered_results


def resolve_rerank_config(
    settings: Settings,
    *,
    top_k: int,
    enable_rerank: bool | None = None,
    reranker: str | None = None,
    rerank_candidate_pool: int | None = None,
) -> RetrievalRerankConfig | None:
    implied_enable = reranker is not None or rerank_candidate_pool is not None
    enabled = settings.enable_rerank if enable_rerank is None else enable_rerank
    enabled = enabled or implied_enable
    if not enabled:
        return None

    reranker_type = (reranker or settings.reranker_type).strip().lower()
    if reranker_type not in {HEURISTIC_RERANKER, BGE_RERANKER_V2_M3, BGE_RERANKER_BASE}:
        raise ValueError(
            f"Unsupported reranker: {reranker_type}. Expected one of "
            f"`{HEURISTIC_RERANKER}`, `{BGE_RERANKER_V2_M3}`, `{BGE_RERANKER_BASE}`."
        )

    candidate_pool = rerank_candidate_pool or settings.rerank_candidate_pool
    candidate_pool = max(candidate_pool, top_k)
    return RetrievalRerankConfig(
        enabled=True,
        reranker_type=reranker_type,
        candidate_pool=candidate_pool,
    )


def detect_query_companies(
    query: str,
    *,
    settings: Settings | None = None,
) -> tuple[list[str], list[str]]:
    query_text = query.lower()
    query_tokens = _tokenize(query_text)
    detected_tickers: list[str] = []
    detected_company_names: list[str] = []

    for entry in _load_company_catalog(settings):
        ticker_detected = entry.ticker.lower() in query_tokens
        alias_detected = any(_alias_in_query(alias, query_text) for alias in entry.aliases)
        if not ticker_detected and not alias_detected:
            continue
        detected_tickers.append(entry.ticker)
        if entry.company_name:
            detected_company_names.append(entry.company_name)

    return detected_tickers, detected_company_names


def detect_comparison_intent(query: str) -> bool:
    normalized_query = f" {query.strip().lower()} "
    return any(phrase in normalized_query for phrase in _COMPARISON_PHRASES)


def rerank_results(
    structured_query: StructuredQuery,
    results: list[RetrievalResult],
    *,
    top_k: int,
    rerank_config: RetrievalRerankConfig | None,
) -> list[RetrievalResult]:
    if not rerank_config:
        return results[:top_k]
    if len(results) <= 1:
        return results[:top_k]
    candidate_results = results[: rerank_config.candidate_pool]
    scores = build_reranker(rerank_config.reranker_type).score(structured_query, candidate_results)

    ranked_pairs = list(zip(scores, candidate_results, strict=True))
    reranked = sorted(
        ranked_pairs,
        key=lambda item: (-item[0], item[1].rank, item[1].chunk_id),
    )[:top_k]
    return [
        replace(
            result,
            rank=rank,
            raw_score=score,
            rerank_score=score,
            retrieval_mode=f"{result.retrieval_mode}_{rerank_config.reranker_type}_rerank",
            source_retrieval_mode=result.retrieval_mode,
        )
        for rank, (score, result) in enumerate(reranked, start=1)
    ]


def build_query_analyzer() -> QueryAnalyzer:
    return DeterministicQueryAnalyzer()


def build_retriever(mode: RetrievalMode) -> Retriever:
    if mode == "lexical":
        return LexicalRetrieverAdapter()
    if mode == "dense":
        return DenseRetrieverAdapter()
    if mode == "hybrid":
        return HybridRetrieverAdapter()
    if mode == "targeted_hybrid":
        return TargetedHybridRetrieverAdapter()
    raise ValueError(f"Unsupported retrieval mode: {mode}")


def build_reranker(reranker_type: str) -> Reranker:
    normalized = reranker_type.strip().lower()
    if normalized == HEURISTIC_RERANKER:
        return HeuristicRerankerAdapter()
    if normalized == BGE_RERANKER_V2_M3:
        return BGERerankerAdapter()
    if normalized == BGE_RERANKER_BASE:
        return BGEBaseRerankerAdapter()
    raise ValueError(
        f"Unsupported reranker: {normalized}. Expected one of "
        f"`{HEURISTIC_RERANKER}`, `{BGE_RERANKER_V2_M3}`, `{BGE_RERANKER_BASE}`."
    )


def warm_retrieval_models(
    settings: Settings,
    *,
    warm_reranker: bool = True,
) -> dict[str, str | None]:
    dense_model = settings.dense_embedding_model
    if settings.dense_index_artifact_path.exists():
        dense_model = load_dense_index_metadata(settings).model

    warmed_dense_model = warm_embedder_model(dense_model)

    warmed_reranker: str | None = None
    reranker_type = settings.reranker_type.strip().lower()
    if warm_reranker and reranker_type == BGE_RERANKER_V2_M3:
        _load_transformer_reranker(_BGE_RERANKER_REPO_ID)
        warmed_reranker = reranker_type
    elif warm_reranker and reranker_type == BGE_RERANKER_BASE:
        _load_transformer_reranker(_BGE_RERANKER_BASE_REPO_ID)
        warmed_reranker = reranker_type

    return {
        "dense_query_model": warmed_dense_model,
        "reranker": warmed_reranker,
    }


@lru_cache(maxsize=8)
def _load_company_catalog(settings: Settings | None) -> tuple[CompanyCatalogEntry, ...]:
    if settings is None:
        return ()

    try:
        _, filings = inspect_corpus(settings)
    except FileNotFoundError:
        return ()

    ticker_to_name: dict[str, str | None] = {}
    ticker_to_aliases: dict[str, set[str]] = {}
    for filing in filings:
        ticker = filing.ticker.strip().upper()
        if not ticker:
            continue
        company_name = filing.company_name.strip() if filing.company_name else None
        if ticker not in ticker_to_name and company_name:
            ticker_to_name[ticker] = company_name
        else:
            ticker_to_name.setdefault(ticker, company_name)
        aliases = ticker_to_aliases.setdefault(ticker, set())
        if company_name:
            aliases.update(_build_company_aliases(company_name))

    return tuple(
        CompanyCatalogEntry(
            ticker=ticker,
            company_name=ticker_to_name.get(ticker),
            aliases=tuple(sorted(ticker_to_aliases.get(ticker, ()), key=len, reverse=True)),
        )
        for ticker in sorted(ticker_to_aliases)
    )


def _in_clause(column: str, values: Iterable[str]) -> str:
    quoted_values = ", ".join(f"'{_escape_sql_string(value)}'" for value in values)
    return f"{column} IN ({quoted_values})"


def _escape_sql_string(value: str) -> str:
    return value.replace("'", "''")


def _normalize_result(row: dict[str, object], *, rank: int, retrieval_mode: str) -> RetrievalResult:
    raw_score_value = row.get("_score") or row.get("_distance")
    raw_score = float(raw_score_value) if raw_score_value is not None else None
    return RetrievalResult(
        chunk_id=str(row["chunk_id"]),
        filing_id=str(row["filing_id"]),
        ticker=str(row["ticker"]),
        form_type=str(row["form_type"]),
        filing_date=str(row["filing_date"]),
        section=_optional_str(row.get("section")),
        section_path=_optional_str(row.get("section_path")),
        text=str(row["text"]),
        raw_score=raw_score,
        retrieval_mode=retrieval_mode,
        rank=rank,
        company_name=_optional_str(row.get("company_name")),
        fiscal_period=_optional_str(row.get("fiscal_period")),
        source_path=_optional_str(row.get("source_path")),
        chunk_index=_optional_int(row.get("chunk_index")),
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _retry_index_update(operation: Callable[[], None], *, attempts: int = 3) -> None:
    for attempt in range(1, attempts + 1):
        try:
            operation()
            return
        except RuntimeError as exc:
            if "Retryable commit conflict" not in str(exc) or attempt == attempts:
                raise
            sleep(0.1 * attempt)


def _artifact_status(settings: Settings, *, dense: bool) -> dict[str, object]:
    table_name = settings.dense_lancedb_table_name if dense else settings.lancedb_table_name
    table_exists = _table_exists(settings.lancedb_dir, table_name)
    status: dict[str, object] = {
        "table_name": table_name,
        "table_exists": table_exists,
        "index_names": [],
    }
    if dense:
        status["metadata_path"] = str(settings.dense_index_artifact_path)
        status["metadata_exists"] = settings.dense_index_artifact_path.exists()

    if not table_exists:
        return status

    table = open_dense_chunk_table(settings) if dense else open_chunk_table(settings)
    status["index_names"] = sorted(index.name for index in table.list_indices())
    return status


def ensure_lexical_retrieval_ready(settings: Settings) -> None:
    prepare_lancedb_artifacts(settings, require_dense=False)
    if _table_exists(settings.lancedb_dir, settings.lancedb_table_name):
        return

    raise LexicalIndexNotReadyError(
        "Lexical retrieval is not ready because the lexical LanceDB table "
        f"`{settings.lancedb_table_name}` is missing. Run `uv run eliza-rag-load-chunks` "
        "before running `eliza-rag-search` or `eliza-rag-answer`, or set "
        "`ELIZA_RAG_LANCEDB_REMOTE_REPO_ID` to auto-download a hosted dataset snapshot. "
        "After any chunk refresh, rerun `uv run eliza-rag-build-dense-index` before dense or hybrid retrieval."
    )


def ensure_dense_retrieval_ready(settings: Settings) -> None:
    prepare_lancedb_artifacts(settings, require_dense=True)
    ensure_lexical_retrieval_ready(settings)
    missing_artifacts: list[str] = []
    if not _table_exists(settings.lancedb_dir, settings.dense_lancedb_table_name):
        missing_artifacts.append(f"dense LanceDB table `{settings.dense_lancedb_table_name}`")
    if not settings.dense_index_artifact_path.exists():
        missing_artifacts.append(f"dense metadata artifact `{settings.dense_index_artifact_path}`")

    if missing_artifacts:
        missing_text = ", ".join(missing_artifacts)
        raise DenseIndexNotReadyError(
            "Dense retrieval is not ready because the following artifact(s) are missing: "
            f"{missing_text}. Run `uv run eliza-rag-build-dense-index` after loading or refreshing "
            f"the lexical chunk table `{settings.lancedb_table_name}`, or configure "
            "`ELIZA_RAG_LANCEDB_REMOTE_REPO_ID` so the repo can fetch a hosted snapshot."
        )


def _table_exists(database_path: Path, table_name: str) -> bool:
    try:
        database = lancedb.connect(database_path)
        database.open_table(table_name)
    except FileNotFoundError:
        return False
    except ValueError:
        return False
    return True


def _build_rerank_query_text(structured_query: StructuredQuery) -> str:
    parts = [
        structured_query.raw_query,
        structured_query.lexical_query,
        structured_query.dense_query,
    ]
    if structured_query.normalized_tickers:
        parts.extend(structured_query.normalized_tickers)
    return " ".join(part for part in parts if part).strip()


def _with_ticker_filter(filters: RetrievalFilters | None, ticker: str) -> RetrievalFilters:
    if filters is None:
        return RetrievalFilters(tickers=[ticker])
    return RetrievalFilters(
        tickers=[ticker],
        form_types=filters.form_types,
        filing_date_from=filters.filing_date_from,
        filing_date_to=filters.filing_date_to,
    )


def _combine_unique(*ticker_lists: list[str] | None) -> list[str]:
    combined: list[str] = []
    seen: set[str] = set()
    for ticker_list in ticker_lists:
        if not ticker_list:
            continue
        for ticker in ticker_list:
            normalized = ticker.strip().upper()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            combined.append(normalized)
    return combined


def _build_company_aliases(company_name: str) -> set[str]:
    aliases = {company_name.lower()}
    normalized_name = " ".join(_ordered_tokens(company_name))
    if normalized_name:
        aliases.add(normalized_name)

    stripped_tokens = _strip_corporate_suffix_tokens(normalized_name.split())
    if stripped_tokens:
        aliases.add(" ".join(stripped_tokens))
        aliases.update(_build_company_alias_prefixes(stripped_tokens))

    return {alias.strip() for alias in aliases if alias.strip()}


def _alias_in_query(alias: str, query_text: str) -> bool:
    query_tokens = " ".join(_ordered_tokens(query_text))
    padded_query = f" {query_tokens} "
    collapsed_query = query_tokens.replace(" ", "")
    alias_tokens = _ordered_tokens(alias)
    if not alias_tokens:
        return False
    normalized_alias = f" {' '.join(alias_tokens)} "
    if normalized_alias in padded_query:
        return True
    if len(alias_tokens) > 1:
        return "".join(alias_tokens) in collapsed_query
    return False


def _strip_corporate_suffix_tokens(tokens: list[str]) -> list[str]:
    stripped_tokens = list(tokens)
    while stripped_tokens and stripped_tokens[-1] in _CORPORATE_SUFFIXES:
        stripped_tokens.pop()
    return stripped_tokens


def _build_company_alias_prefixes(tokens: list[str]) -> set[str]:
    aliases: set[str] = set()
    for length in range(1, len(tokens)):
        prefix = tokens[:length]
        if prefix[-1] in _ALIAS_STOPWORDS:
            continue
        if len(prefix) == 1 and not _is_distinctive_single_token_alias(prefix[0]):
            continue
        aliases.add(" ".join(prefix))
    return aliases


def _is_distinctive_single_token_alias(token: str) -> bool:
    return len(token) >= 5 and token not in _GENERIC_SINGLE_TOKEN_ALIASES


def _score_result_for_rerank(
    result: RetrievalResult,
    *,
    query_terms: set[str],
    query_text: str,
) -> float:
    document_text = " ".join(
        filter(
            None,
            [
                result.ticker,
                result.company_name,
                result.section,
                result.section_path,
                result.text,
            ],
        )
    ).lower()
    document_terms = _tokenize(document_text)
    overlap = len(query_terms & document_terms)
    coverage = overlap / max(len(query_terms), 1)

    score = overlap + (coverage * 10.0)
    if query_text and query_text in document_text:
        score += 5.0
    if result.ticker.lower() in query_text:
        score += 3.0
    if result.company_name:
        company_terms = _tokenize(result.company_name.lower()) - {"inc", "corp", "co", "group", "plc"}
        score += min(len(company_terms & query_terms), 2) * 1.5
    if "risk" in query_terms and any(
        phrase in document_text for phrase in ("risk factors", "risk factor", "item 1a")
    ):
        score += 2.0

    # Preserve some bias toward the original retrieval order as a low-weight tie-breaker.
    score += 1.0 / (50 + result.rank)
    return score


def _tokenize(text: str) -> set[str]:
    return {match.group(0) for match in _TOKEN_RE.finditer(text.lower())}


def _ordered_tokens(text: str) -> list[str]:
    return [match.group(0) for match in _TOKEN_RE.finditer(text.lower())]


def _score_with_bge_reranker(query: str, results: list[RetrievalResult]) -> list[float]:
    return _score_with_transformer_reranker(query, results, repo_id=_BGE_RERANKER_REPO_ID)


def _score_with_transformer_reranker(
    query: str,
    results: list[RetrievalResult],
    *,
    repo_id: str,
) -> list[float]:
    tokenizer, model, device = _load_transformer_reranker(repo_id)
    pairs = [(query, result.text) for result in results]
    batch_size = 8
    scores: list[float] = []

    try:
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "torch is required for the BGE reranker. Run `uv sync` to install project dependencies."
        ) from exc

    for start in range(0, len(pairs), batch_size):
        batch_pairs = pairs[start : start + batch_size]
        encoded = tokenizer(
            batch_pairs,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        encoded = {key: value.to(device) for key, value in encoded.items()}
        with torch.inference_mode():
            logits = model(**encoded).logits.view(-1).float().cpu().tolist()
        scores.extend(float(value) for value in logits)
    return scores


@lru_cache(maxsize=4)
def _load_transformer_reranker(repo_id: str):
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "transformers and torch are required for the BGE reranker. "
            "Run `uv sync` to install project dependencies."
        ) from exc

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(repo_id)
    model = AutoModelForSequenceClassification.from_pretrained(repo_id)
    model.eval()
    model.to(device)
    return tokenizer, model, device
