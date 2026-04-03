from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class FilingRecord:
    filing_id: str
    ticker: str
    form_type: str
    filing_date: str
    fiscal_period: str | None
    source_path: str
    raw_text: str
    company_name: str | None = None
    report_period: str | None = None
    cik: str | None = None
    manifest_listed: bool | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ChunkRecord:
    chunk_id: str
    filing_id: str
    ticker: str
    form_type: str
    filing_date: str
    fiscal_period: str | None
    source_path: str
    chunk_index: int
    text: str
    company_name: str | None = None
    section: str | None = None
    section_path: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RetrievalFilters:
    tickers: list[str] | None = None
    form_types: list[str] | None = None
    filing_date_from: str | None = None
    filing_date_to: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RetrievalRerankConfig:
    enabled: bool
    reranker_type: str
    candidate_pool: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class StructuredQuery:
    raw_query: str
    retrieval_text: str
    lexical_query: str
    dense_query: str
    expansion_terms: list[str]
    normalized_tickers: list[str] | None = None
    detected_tickers: list[str] | None = None
    detected_company_names: list[str] | None = None
    target_tickers: list[str] | None = None
    filing_date_from: str | None = None
    filing_date_to: str | None = None
    is_multi_company: bool = False
    is_comparison_query: bool = False
    requires_entity_coverage: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RetrievalResult:
    chunk_id: str
    filing_id: str
    ticker: str
    form_type: str
    filing_date: str
    section: str | None
    section_path: str | None
    text: str
    raw_score: float | None
    retrieval_mode: str
    rank: int
    company_name: str | None = None
    fiscal_period: str | None = None
    source_path: str | None = None
    chunk_index: int | None = None
    rerank_score: float | None = None
    source_retrieval_mode: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class AnswerCitation:
    citation_id: str
    chunk_id: str
    filing_id: str
    ticker: str
    company_name: str | None
    form_type: str
    filing_date: str
    section: str | None
    source_path: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class AnswerFinding:
    statement: str
    citations: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class AnswerResponse:
    question: str
    answer: str
    summary: str
    findings: list[AnswerFinding]
    uncertainty: str
    citations: list[AnswerCitation]
    retrieval_mode: str
    prompt_path: str
    prompt_preview: str
    prompt_characters: int
    retrieval_results: list[RetrievalResult]
    raw_model_response: str
    model: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["findings"] = [finding.to_dict() for finding in self.findings]
        payload["citations"] = [citation.to_dict() for citation in self.citations]
        payload["retrieval_results"] = [result.to_dict() for result in self.retrieval_results]
        return payload


@dataclass(slots=True)
class CorpusInspection:
    corpus_dir: str
    manifest_path: str | None
    manifest_present: bool
    manifest_file_count: int | None
    discovered_file_count: int
    tickers: list[str]
    filing_types: dict[str, int]
    filing_date_range: dict[str, str | None]
    manifest_missing_files: list[str]
    unlisted_files: list[str]
    filename_parse_failures: list[str]
    sample_filing_ids: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
