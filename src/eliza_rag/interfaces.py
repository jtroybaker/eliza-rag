from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .config import Settings
from .models import RetrievalFilters, RetrievalResult, StructuredQuery

if TYPE_CHECKING:
    from .embeddings import DenseIndexMetadata


class Embedder(Protocol):
    def build_document_vectors(
        self,
        settings: Settings,
        texts: list[str],
    ) -> tuple[DenseIndexMetadata, list[list[float]]]:
        ...

    def encode_query(
        self,
        text: str,
        metadata: DenseIndexMetadata,
    ) -> list[float]:
        ...


class Reranker(Protocol):
    @property
    def name(self) -> str:
        ...

    def score(
        self,
        structured_query: StructuredQuery,
        results: list[RetrievalResult],
    ) -> list[float]:
        ...


class QueryAnalyzer(Protocol):
    def analyze(
        self,
        query: str,
        *,
        filters: RetrievalFilters | None = None,
        settings: Settings | None = None,
    ) -> StructuredQuery:
        ...


class Retriever(Protocol):
    @property
    def mode(self) -> str:
        ...

    def retrieve(
        self,
        settings: Settings,
        structured_query: StructuredQuery,
        *,
        top_k: int | None = None,
        filters: RetrievalFilters | None = None,
        phrase_query: bool = False,
    ) -> list[RetrievalResult]:
        ...


class AnswerBackend(Protocol):
    @property
    def model(self) -> str:
        ...

    def generate(self, prompt: str) -> str:
        ...
