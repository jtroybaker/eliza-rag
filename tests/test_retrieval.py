from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from eliza_rag.config import Settings, get_settings
from eliza_rag.models import ChunkRecord, RetrievalFilters, RetrievalResult
from eliza_rag.embeddings import DenseIndexMetadata
from eliza_rag.retrieval import (
    BGE_RERANKER_BASE,
    BGE_RERANKER_V2_M3,
    CompanyCatalogEntry,
    DENSE_RETRIEVAL_MODE,
    DenseIndexNotReadyError,
    HEURISTIC_RERANKER,
    HYBRID_RETRIEVAL_MODE,
    LEXICAL_RETRIEVAL_MODE,
    LexicalIndexNotReadyError,
    TARGETED_HYBRID_RETRIEVAL_MODE,
    analyze_query,
    build_query_analyzer,
    build_reranker,
    build_retriever,
    build_filter_sql,
    detect_comparison_intent,
    detect_query_companies,
    index_status,
    retrieve,
    retrieve_dense,
    retrieve_lexical,
)
from eliza_rag.storage import build_dense_index, load_chunk_records


@pytest.fixture(scope="module")
def dense_index_ready() -> None:
    build_dense_index(
        replace(
            get_settings(),
            dense_embedding_model="hashed_v1",
            dense_embedding_dim=256,
        )
    )


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "repo_root": tmp_path,
        "data_dir": tmp_path / "data",
        "artifacts_dir": tmp_path / "artifacts",
        "prompts_dir": tmp_path / "prompts",
        "quality_notes_path": tmp_path / "docs" / "agents" / "QUALITY_NOTES.md",
        "prompt_iteration_log_path": tmp_path / "docs" / "agents" / "PROMPT_ITERATION_LOG.md",
        "corpus_dir": tmp_path / "edgar_corpus",
        "corpus_zip_path": tmp_path / "edgar_corpus.zip",
        "lancedb_dir": tmp_path / "data" / "lancedb",
        "lancedb_table_name": "filing_chunks",
        "dense_lancedb_table_name": "filing_chunks_dense",
        "dense_index_artifact_name": "dense_index_metadata.json",
        "lancedb_remote_repo_id": None,
        "lancedb_remote_repo_type": "dataset",
        "lancedb_remote_revision": None,
        "lancedb_remote_token": None,
        "lancedb_remote_auto_download": True,
        "lancedb_archive_url": None,
        "lancedb_archive_auto_download": True,
        "chunk_size_tokens": 800,
        "chunk_overlap_tokens": 100,
        "retrieval_top_k": 8,
        "answer_top_k": 6,
        "enable_rerank": False,
        "reranker_type": "heuristic",
        "rerank_candidate_pool": 12,
        "dense_embedding_model": "hashed_v1",
        "dense_embedding_dim": 256,
        "dense_index_metric": "cosine",
        "llm_provider": "openai",
        "llm_base_url": "https://api.openai.com/v1",
        "llm_api_key": None,
        "llm_model": "gpt-5-mini",
        "local_llm_runtime": "ollama",
        "local_llm_runtime_command": "ollama",
        "local_llm_base_url": "http://127.0.0.1:11434/v1",
        "local_llm_model": "qwen2.5:3b-instruct",
        "local_llm_start_timeout_seconds": 1,
    }
    values.update(overrides)
    return Settings(**values)


def test_build_filter_sql_combines_supported_filters() -> None:
    filters = RetrievalFilters(
        tickers=["AAPL", "MSFT"],
        form_types=["10-K"],
        filing_date_from="2024-01-01",
        filing_date_to="2025-12-31",
    )

    assert build_filter_sql(filters) == (
        "ticker IN ('AAPL', 'MSFT') AND form_type IN ('10-K') "
        "AND filing_date >= '2024-01-01' AND filing_date <= '2025-12-31'"
    )


def test_retrieve_lexical_returns_normalized_results() -> None:
    settings = get_settings()

    results = retrieve_lexical(
        settings,
        "risk factors",
        top_k=3,
        filters=RetrievalFilters(tickers=["AAPL"]),
        phrase_query=True,
    )

    assert len(results) == 3
    assert [result.rank for result in results] == [1, 2, 3]
    assert all(result.retrieval_mode == LEXICAL_RETRIEVAL_MODE for result in results)
    assert all(result.ticker == "AAPL" for result in results)
    assert all(result.chunk_id for result in results)
    assert all(result.text for result in results)


def test_retrieve_lexical_applies_date_and_form_filters() -> None:
    settings = get_settings()

    results = retrieve_lexical(
        settings,
        "revenue growth",
        top_k=5,
        filters=RetrievalFilters(
            tickers=["GOOG"],
            form_types=["10-K"],
            filing_date_from="2025-01-01",
            filing_date_to="2025-12-31",
        ),
    )

    assert results
    assert all(result.ticker == "GOOG" for result in results)
    assert all(result.form_type == "10-K" for result in results)
    assert all("2025-01-01" <= result.filing_date <= "2025-12-31" for result in results)


def test_analyze_query_adds_dense_expansion_and_year_bounds() -> None:
    structured = analyze_query("AAPL revenue risk 2024")

    assert structured.lexical_query == "AAPL revenue risk 2024"
    assert "sales" not in structured.expansion_terms
    assert structured.filing_date_from == "2024-01-01"
    assert structured.filing_date_to == "2024-12-31"


def test_build_query_analyzer_preserves_deterministic_default() -> None:
    analyzer = build_query_analyzer()

    structured = analyzer.analyze("AAPL revenue risk 2024")

    assert structured.lexical_query == "AAPL revenue risk 2024"
    assert structured.filing_date_from == "2024-01-01"


def test_analyze_query_detects_companies_and_comparison_intent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "eliza_rag.retrieval._load_company_catalog",
        lambda settings: (
            CompanyCatalogEntry("AAPL", "Apple Inc.", ("apple inc", "apple")),
            CompanyCatalogEntry("TSLA", "Tesla, Inc.", ("tesla inc", "tesla")),
        ),
    )

    structured = analyze_query(
        "What are the primary risk factors facing Apple and Tesla, and how do they compare?",
        settings=get_settings(),
    )

    assert structured.detected_tickers == ["AAPL", "TSLA"]
    assert structured.detected_company_names == ["Apple Inc.", "Tesla, Inc."]
    assert structured.target_tickers == ["AAPL", "TSLA"]
    assert structured.is_multi_company is True
    assert structured.is_comparison_query is True
    assert structured.requires_entity_coverage is True


def test_analyze_query_detects_financial_company_alias_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "eliza_rag.retrieval._load_company_catalog",
        lambda settings: (
            CompanyCatalogEntry("AAPL", "Apple Inc.", ("apple inc", "apple")),
            CompanyCatalogEntry("TSLA", "Tesla, Inc.", ("tesla inc", "tesla")),
            CompanyCatalogEntry(
                "JPM",
                "JPMorgan Chase & Co.",
                ("jpmorgan chase co", "jpmorgan chase", "jpmorgan"),
            ),
        ),
    )

    structured = analyze_query(
        "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?",
        settings=get_settings(),
    )

    assert structured.detected_tickers == ["AAPL", "TSLA", "JPM"]
    assert structured.target_tickers == ["AAPL", "TSLA", "JPM"]
    assert structured.requires_entity_coverage is True


def test_detect_query_companies_handles_bank_of_america_variant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "eliza_rag.retrieval._load_company_catalog",
        lambda settings: (
            CompanyCatalogEntry(
                "JPM",
                "JPMorgan Chase & Co.",
                ("jpmorgan chase co", "jpmorgan chase", "jpmorgan"),
            ),
            CompanyCatalogEntry(
                "BAC",
                "Bank of America Corporation",
                ("bank of america corporation", "bank of america"),
            ),
        ),
    )

    detected_tickers, detected_names = detect_query_companies(
        "What are the primary risk factors facing JPMorgan and Bank of America, and how do they compare?",
        settings=get_settings(),
    )

    assert detected_tickers == ["JPM", "BAC"]
    assert detected_names == ["JPMorgan Chase & Co.", "Bank of America Corporation"]


def test_detect_query_companies_avoids_generic_single_word_overmatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "eliza_rag.retrieval._load_company_catalog",
        lambda settings: (
            CompanyCatalogEntry(
                "BAC",
                "Bank of America Corporation",
                ("bank of america corporation", "bank of america"),
            ),
        ),
    )

    detected_tickers, detected_names = detect_query_companies(
        "How do banks describe interest rate risk in annual filings?",
        settings=get_settings(),
    )

    assert detected_tickers == []
    assert detected_names == []


def test_detect_comparison_intent_is_false_for_single_company_lookup() -> None:
    assert detect_comparison_intent("What risk factors does Apple describe?") is False


def test_retrieve_dense_uses_metadata_model_for_query_encoding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path, dense_embedding_model="Snowflake/snowflake-arctic-embed-xs")
    observed: dict[str, object] = {}

    monkeypatch.setattr("eliza_rag.retrieval.ensure_dense_retrieval_ready", lambda settings: None)
    monkeypatch.setattr(
        "eliza_rag.retrieval.ensure_dense_indices",
        lambda settings: {"table_name": settings.dense_lancedb_table_name},
    )
    monkeypatch.setattr(
        "eliza_rag.retrieval.load_dense_index_metadata",
        lambda settings: DenseIndexMetadata(
            model="hashed_v1",
            dimension=3,
            document_count=10,
            document_frequency_by_bucket=[1, 1, 1],
        ),
    )
    monkeypatch.setattr(
        "eliza_rag.retrieval.encode_text",
        lambda query, metadata: observed.update(
            {"query": query, "metadata_model": metadata.model}
        )
        or [0.1, 0.2, 0.3],
    )

    class _Search:
        def metric(self, metric: str):
            observed["metric"] = metric
            return self

        def limit(self, limit: int):
            observed["limit"] = limit
            return self

        def to_list(self):
            return []

    class _Table:
        def search(self, query_vector, vector_column_name: str):
            observed["query_vector"] = query_vector
            observed["vector_column_name"] = vector_column_name
            return _Search()

    monkeypatch.setattr("eliza_rag.retrieval.open_dense_chunk_table", lambda settings: _Table())

    retrieve_dense(settings, "Apple risk factors", top_k=4)

    assert observed["metadata_model"] == "hashed_v1"
    assert observed["vector_column_name"] == "vector"
    assert observed["limit"] == 4


def test_retrieve_dense_raises_clear_error_when_dense_index_is_missing(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    load_chunk_records(
        settings,
        [
            ChunkRecord(
                chunk_id="AAPL::chunk-0001",
                filing_id="AAPL_10K_2024",
                ticker="AAPL",
                company_name="Apple Inc.",
                form_type="10-K",
                filing_date="2024-11-01",
                fiscal_period="2024Q4",
                source_path="edgar_corpus/AAPL_10K_2024_full.txt",
                section="Risk Factors",
                section_path="Item 1A",
                chunk_index=0,
                text="Apple faces supply chain, regulatory, and competitive risks.",
            )
        ],
    )

    with pytest.raises(DenseIndexNotReadyError, match="Run `uv run eliza-rag-build-dense-index`"):
        retrieve(
            settings,
            "risk factors",
            mode="dense",
            top_k=3,
            filters=RetrievalFilters(tickers=["AAPL"]),
        )


def test_retrieve_lexical_raises_clear_error_when_chunk_table_is_missing(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    with pytest.raises(LexicalIndexNotReadyError, match="Run `uv run eliza-rag-load-chunks`"):
        retrieve(
            settings,
            "risk factors",
            mode="lexical",
            top_k=3,
            filters=RetrievalFilters(tickers=["AAPL"]),
        )


def test_index_status_reports_missing_tables_and_dense_metadata(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    status = index_status(settings)

    assert status["lexical"] == {
        "table_name": "filing_chunks",
        "table_exists": False,
        "index_names": [],
    }
    assert status["dense"] == {
        "table_name": "filing_chunks_dense",
        "table_exists": False,
        "index_names": [],
        "metadata_path": str(tmp_path / "artifacts" / "dense_index_metadata.json"),
        "metadata_exists": False,
    }


def test_retrieve_dense_returns_normalized_results(dense_index_ready: None) -> None:
    settings = get_settings()

    results = retrieve_dense(
        settings,
        "risk factors",
        top_k=3,
        filters=RetrievalFilters(tickers=["AAPL"]),
    )

    assert len(results) == 3
    assert [result.rank for result in results] == [1, 2, 3]
    assert all(result.retrieval_mode == DENSE_RETRIEVAL_MODE for result in results)
    assert all(result.ticker == "AAPL" for result in results)
    assert all(result.chunk_id for result in results)
    assert all(result.text for result in results)


def test_retrieve_hybrid_compares_modes_under_one_interface(dense_index_ready: None) -> None:
    settings = get_settings()

    lexical_results = retrieve(
        settings,
        "revenue growth",
        mode="lexical",
        top_k=3,
        filters=RetrievalFilters(tickers=["GOOG"]),
    )
    dense_results = retrieve(
        settings,
        "revenue growth",
        mode="dense",
        top_k=3,
        filters=RetrievalFilters(tickers=["GOOG"]),
    )
    hybrid_results = retrieve(
        settings,
        "revenue growth",
        mode="hybrid",
        top_k=3,
        filters=RetrievalFilters(tickers=["GOOG"]),
    )

    assert lexical_results and dense_results and hybrid_results
    assert all(result.retrieval_mode == LEXICAL_RETRIEVAL_MODE for result in lexical_results)
    assert all(result.retrieval_mode == DENSE_RETRIEVAL_MODE for result in dense_results)
    assert all(result.retrieval_mode == HYBRID_RETRIEVAL_MODE for result in hybrid_results)
    assert [result.rank for result in hybrid_results] == [1, 2, 3]
    assert all(result.ticker == "GOOG" for result in hybrid_results)


def test_build_retriever_exposes_all_default_modes() -> None:
    assert build_retriever("lexical").mode == "lexical"
    assert build_retriever("dense").mode == "dense"
    assert build_retriever("hybrid").mode == "hybrid"
    assert build_retriever("targeted_hybrid").mode == "targeted_hybrid"


def test_retrieve_can_rerank_candidates(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    base_results = [
        ChunkRecord(
            chunk_id="GENERIC::chunk-0001",
            filing_id="GENERIC_10K_2025",
            ticker="GENERIC",
            company_name="Generic Corp",
            form_type="10-K",
            filing_date="2025-01-01",
            fiscal_period="2024Q4",
            source_path="generic.txt",
            section="Overview",
            section_path="Item 1",
            chunk_index=0,
            text="General business overview with little discussion of specific risks.",
        ),
        ChunkRecord(
            chunk_id="AAPL::chunk-0002",
            filing_id="AAPL_10K_2025",
            ticker="AAPL",
            company_name="Apple Inc.",
            form_type="10-K",
            filing_date="2025-01-31",
            fiscal_period="2024Q4",
            source_path="aapl.txt",
            section="Risk Factors",
            section_path="Item 1A",
            chunk_index=1,
            text="Apple discusses supply chain concentration and competition risk factors.",
        ),
    ]
    normalized_results = [
        RetrievalResult(
            chunk_id=row.chunk_id,
            filing_id=row.filing_id,
            ticker=row.ticker,
            form_type=row.form_type,
            filing_date=row.filing_date,
            section=row.section,
            section_path=row.section_path,
            text=row.text,
            raw_score=1.0,
            retrieval_mode=LEXICAL_RETRIEVAL_MODE,
            rank=index,
            company_name=row.company_name,
            fiscal_period=row.fiscal_period,
            source_path=row.source_path,
            chunk_index=row.chunk_index,
        )
        for index, row in enumerate(base_results, start=1)
    ]

    monkeypatch.setattr("eliza_rag.retrieval.retrieve_lexical", lambda *args, **kwargs: normalized_results)
    monkeypatch.setattr(
        "eliza_rag.retrieval._score_with_bge_reranker",
        lambda query, results: [0.1, 0.9],
    )

    reranked = retrieve(
        settings,
        "Apple risk factors",
        mode="lexical",
        top_k=2,
        enable_rerank=True,
        reranker=BGE_RERANKER_V2_M3,
        rerank_candidate_pool=2,
    )

    assert [result.chunk_id for result in reranked] == ["AAPL::chunk-0002", "GENERIC::chunk-0001"]
    assert reranked[0].retrieval_mode == "lexical_bge-reranker-v2-m3_rerank"
    assert reranked[0].source_retrieval_mode == LEXICAL_RETRIEVAL_MODE
    assert reranked[0].rerank_score is not None


def test_retrieve_can_still_use_heuristic_reranker(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    normalized_results = [
        RetrievalResult(
            chunk_id="GENERIC::chunk-0001",
            filing_id="GENERIC_10K_2025",
            ticker="GENERIC",
            form_type="10-K",
            filing_date="2025-01-01",
            section="Overview",
            section_path="Item 1",
            text="General business overview with little discussion of specific risks.",
            raw_score=1.0,
            retrieval_mode=LEXICAL_RETRIEVAL_MODE,
            rank=1,
            company_name="Generic Corp",
        ),
        RetrievalResult(
            chunk_id="AAPL::chunk-0002",
            filing_id="AAPL_10K_2025",
            ticker="AAPL",
            form_type="10-K",
            filing_date="2025-01-31",
            section="Risk Factors",
            section_path="Item 1A",
            text="Apple discusses supply chain concentration and competition risk factors.",
            raw_score=1.0,
            retrieval_mode=LEXICAL_RETRIEVAL_MODE,
            rank=2,
            company_name="Apple Inc.",
        ),
    ]

    monkeypatch.setattr("eliza_rag.retrieval.retrieve_lexical", lambda *args, **kwargs: normalized_results)

    reranked = retrieve(
        settings,
        "Apple risk factors",
        mode="lexical",
        top_k=2,
        enable_rerank=True,
        reranker=HEURISTIC_RERANKER,
        rerank_candidate_pool=2,
    )

    assert [result.chunk_id for result in reranked] == ["AAPL::chunk-0002", "GENERIC::chunk-0001"]
    assert reranked[0].retrieval_mode == "lexical_heuristic_rerank"


def test_retrieve_can_use_alternate_transformer_reranker(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    normalized_results = [
        RetrievalResult(
            chunk_id="GENERIC::chunk-0001",
            filing_id="GENERIC_10K_2025",
            ticker="GENERIC",
            form_type="10-K",
            filing_date="2025-01-01",
            section="Overview",
            section_path="Item 1",
            text="General business overview.",
            raw_score=1.0,
            retrieval_mode=LEXICAL_RETRIEVAL_MODE,
            rank=1,
            company_name="Generic Corp",
        ),
        RetrievalResult(
            chunk_id="AAPL::chunk-0002",
            filing_id="AAPL_10K_2025",
            ticker="AAPL",
            form_type="10-K",
            filing_date="2025-01-31",
            section="Risk Factors",
            section_path="Item 1A",
            text="Apple risk factors.",
            raw_score=1.0,
            retrieval_mode=LEXICAL_RETRIEVAL_MODE,
            rank=2,
            company_name="Apple Inc.",
        ),
    ]

    monkeypatch.setattr("eliza_rag.retrieval.retrieve_lexical", lambda *args, **kwargs: normalized_results)
    monkeypatch.setattr(
        "eliza_rag.retrieval._score_with_transformer_reranker",
        lambda query, results, repo_id: [0.2, 0.8],
    )

    reranked = retrieve(
        settings,
        "Apple risk factors",
        mode="lexical",
        top_k=2,
        enable_rerank=True,
        reranker=BGE_RERANKER_BASE,
        rerank_candidate_pool=2,
    )

    assert [result.chunk_id for result in reranked] == ["AAPL::chunk-0002", "GENERIC::chunk-0001"]
    assert reranked[0].retrieval_mode == "lexical_bge-reranker-base_rerank"


def test_build_reranker_exposes_current_default_adapters() -> None:
    assert build_reranker(HEURISTIC_RERANKER).name == HEURISTIC_RERANKER
    assert build_reranker(BGE_RERANKER_V2_M3).name == BGE_RERANKER_V2_M3


def test_retrieve_uses_configured_rerank_candidate_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(
        Path("."),
        repo_root=Path("."),
        data_dir=Path("data"),
        artifacts_dir=Path("artifacts"),
        prompts_dir=Path("prompts"),
        corpus_dir=Path("edgar_corpus"),
        corpus_zip_path=Path("edgar_corpus.zip"),
        lancedb_dir=Path("data/lancedb"),
        enable_rerank=True,
        reranker_type=BGE_RERANKER_V2_M3,
        rerank_candidate_pool=7,
    )
    observed: dict[str, object] = {}
    fake_results = [
        RetrievalResult(
            chunk_id="AAPL::chunk-0001",
            filing_id="AAPL_10K_2025",
            ticker="AAPL",
            form_type="10-K",
            filing_date="2025-01-31",
            section="Risk Factors",
            section_path="Item 1A",
            text="Apple risk factors.",
            raw_score=1.0,
            retrieval_mode=HYBRID_RETRIEVAL_MODE,
            rank=1,
        )
    ]

    def _fake_retrieve_hybrid(*args, **kwargs):
        observed["top_k"] = kwargs["top_k"]
        return fake_results

    monkeypatch.setattr("eliza_rag.retrieval.retrieve_hybrid", _fake_retrieve_hybrid)

    results = retrieve(settings, "Apple risk factors", mode="hybrid", top_k=3)

    assert observed["top_k"] == 7
    assert results == fake_results


def test_targeted_hybrid_preserves_candidate_coverage(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()

    monkeypatch.setattr(
        "eliza_rag.retrieval._load_company_catalog",
        lambda current_settings: (
            CompanyCatalogEntry("AAPL", "Apple Inc.", ("apple inc", "apple")),
            CompanyCatalogEntry("TSLA", "Tesla, Inc.", ("tesla inc", "tesla")),
        ),
    )

    def _result(ticker: str, rank: int) -> RetrievalResult:
        company_name = "Apple Inc." if ticker == "AAPL" else "Tesla, Inc."
        return RetrievalResult(
            chunk_id=f"{ticker}::chunk-{rank:04d}",
            filing_id=f"{ticker}_10K_2025",
            ticker=ticker,
            form_type="10-K",
            filing_date="2025-01-31",
            section="Risk Factors",
            section_path="Item 1A",
            text=f"{company_name} risk factors {rank}.",
            raw_score=1.0 / rank,
            retrieval_mode=HYBRID_RETRIEVAL_MODE,
            rank=rank,
            company_name=company_name,
        )

    def _fake_retrieve_hybrid(*args, **kwargs):
        filters = kwargs.get("filters")
        if filters and filters.tickers == ["AAPL"]:
            return [_result("AAPL", 1), _result("AAPL", 2)]
        if filters and filters.tickers == ["TSLA"]:
            return [_result("TSLA", 1), _result("TSLA", 2)]
        return [_result("AAPL", 1), _result("TSLA", 1), _result("AAPL", 2), _result("TSLA", 2)]

    monkeypatch.setattr("eliza_rag.retrieval.retrieve_hybrid", _fake_retrieve_hybrid)

    results = retrieve(
        settings,
        "Compare the main risk factors facing Apple and Tesla",
        mode="targeted_hybrid",
        top_k=4,
    )

    assert [result.ticker for result in results] == ["AAPL", "TSLA", "AAPL", "TSLA"]
    assert all(result.retrieval_mode == TARGETED_HYBRID_RETRIEVAL_MODE for result in results)
