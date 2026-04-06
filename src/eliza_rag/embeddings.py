from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from .config import Settings

if TYPE_CHECKING:
    from .interfaces import Embedder

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9&.\-]{1,}")
DEFAULT_EMBEDDING_MODEL = "hashed_v1"
DEFAULT_EXTERNAL_EMBEDDING_MODEL = "Snowflake/snowflake-arctic-embed-xs"
BGE_M3_EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDER_ALIASES = {
    "hashed_v1": DEFAULT_EMBEDDING_MODEL,
    "snowflake-arctic-embed-xs": DEFAULT_EXTERNAL_EMBEDDING_MODEL,
    "bge-m3": BGE_M3_EMBEDDING_MODEL,
}
_SYNONYM_MAP = {
    "danger": ("risk",),
    "hazard": ("risk",),
    "sales": ("revenue",),
    "turnover": ("revenue",),
    "income": ("profit", "earnings"),
    "ai": ("artificial", "intelligence"),
    "regulation": ("regulatory",),
    "lawsuit": ("litigation",),
}


@dataclass(slots=True)
class DenseIndexMetadata:
    model: str
    dimension: int
    document_count: int
    document_frequency_by_bucket: list[int]

    def to_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "dimension": self.dimension,
            "document_count": self.document_count,
            "document_frequency_by_bucket": self.document_frequency_by_bucket,
        }


class EmbeddingError(RuntimeError):
    """Raised when dense embedding generation fails."""


def available_embedder_choices() -> tuple[str, ...]:
    return tuple(EMBEDDER_ALIASES)


def resolve_embedder_model(selection: str) -> str:
    normalized = selection.strip()
    return EMBEDDER_ALIASES.get(normalized.lower(), normalized)


def resolve_embedder_alias(selection: str) -> str:
    resolved_model = resolve_embedder_model(selection)
    for alias, model in EMBEDDER_ALIASES.items():
        if model == resolved_model:
            return alias
    return selection.strip()


class HashedBaselineEmbedder:
    def build_document_vectors(
        self,
        settings: Settings,
        texts: list[str],
    ) -> tuple[DenseIndexMetadata, list[list[float]]]:
        metadata = build_dense_index_metadata(
            texts,
            dimension=settings.dense_embedding_dim,
            model=DEFAULT_EMBEDDING_MODEL,
        )
        return metadata, [self.encode_query(text, metadata) for text in texts]

    def encode_query(self, text: str, metadata: DenseIndexMetadata) -> list[float]:
        buckets = [0.0] * metadata.dimension
        term_frequency: dict[str, int] = {}

        for feature in _iter_features(text):
            term_frequency[feature] = term_frequency.get(feature, 0) + 1

        if not term_frequency:
            return buckets

        for feature, frequency in term_frequency.items():
            bucket, sign = _feature_bucket_and_sign(feature, metadata.dimension)
            document_frequency = metadata.document_frequency_by_bucket[bucket]
            inverse_document_frequency = math.log((metadata.document_count + 1) / (document_frequency + 1)) + 1.0
            buckets[bucket] += sign * float(frequency) * inverse_document_frequency

        norm = math.sqrt(sum(value * value for value in buckets))
        if norm == 0.0:
            return buckets

        return [value / norm for value in buckets]


class SentenceTransformerEmbedder:
    def __init__(self, *, model: str) -> None:
        self._model = model

    def build_document_vectors(
        self,
        settings: Settings,
        texts: list[str],
    ) -> tuple[DenseIndexMetadata, list[list[float]]]:
        vectors = _encode_texts_with_sentence_transformer(texts, model=self._model)
        if not vectors:
            raise EmbeddingError(f"Embedding model `{self._model}` returned no vectors.")

        metadata = DenseIndexMetadata(
            model=self._model,
            dimension=len(vectors[0]),
            document_count=len(texts),
            document_frequency_by_bucket=[],
        )
        return metadata, vectors

    def encode_query(self, text: str, metadata: DenseIndexMetadata) -> list[float]:
        vectors = _encode_texts_with_sentence_transformer([text], model=metadata.model)
        if not vectors:
            raise EmbeddingError(f"Embedding model `{metadata.model}` returned no query vector.")
        vector = vectors[0]
        if len(vector) != metadata.dimension:
            raise EmbeddingError(
                f"Embedding dimension mismatch for `{metadata.model}`: "
                f"index expects {metadata.dimension}, query returned {len(vector)}."
            )
        return vector


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def expand_query_terms(query: str) -> list[str]:
    expansions: list[str] = []
    for token in tokenize(query):
        expansions.extend(_SYNONYM_MAP.get(token, ()))
    return sorted(set(expansions))


def build_dense_index_metadata(
    texts: list[str],
    *,
    dimension: int,
    model: str = DEFAULT_EMBEDDING_MODEL,
) -> DenseIndexMetadata:
    if model != DEFAULT_EMBEDDING_MODEL:
        raise ValueError(
            "build_dense_index_metadata only supports the local hashed baseline. "
            "Use `build_dense_vectors` for external embedding models."
        )
    bucket_document_frequency = [0] * dimension
    for text in texts:
        seen_buckets: set[int] = set()
        for feature in _iter_features(text):
            bucket, _ = _feature_bucket_and_sign(feature, dimension)
            seen_buckets.add(bucket)
        for bucket in seen_buckets:
            bucket_document_frequency[bucket] += 1

    return DenseIndexMetadata(
        model=model,
        dimension=dimension,
        document_count=len(texts),
        document_frequency_by_bucket=bucket_document_frequency,
    )


def encode_text(text: str, metadata: DenseIndexMetadata) -> list[float]:
    if metadata.model != DEFAULT_EMBEDDING_MODEL:
        return SentenceTransformerEmbedder(model=metadata.model).encode_query(text, metadata)
    return HashedBaselineEmbedder().encode_query(text, metadata)


def write_dense_index_metadata(path: Path, metadata: DenseIndexMetadata) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata.to_dict(), indent=2), encoding="utf-8")
    return path


def read_dense_index_metadata(path: Path) -> DenseIndexMetadata:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return DenseIndexMetadata(
        model=str(payload["model"]),
        dimension=int(payload["dimension"]),
        document_count=int(payload["document_count"]),
        document_frequency_by_bucket=[int(value) for value in payload["document_frequency_by_bucket"]],
    )


def load_dense_index_metadata(settings: Settings) -> DenseIndexMetadata:
    return read_dense_index_metadata(settings.dense_index_artifact_path)


def build_dense_vectors(settings: Settings, texts: list[str]) -> tuple[DenseIndexMetadata, list[list[float]]]:
    return resolve_embedder(settings).build_document_vectors(settings, texts)


def resolve_embedder(settings: Settings) -> Embedder:
    return resolve_embedder_for_model(settings.dense_embedding_model)


def resolve_embedder_for_model(selection: str) -> Embedder:
    model = resolve_embedder_model(selection)
    if model == DEFAULT_EMBEDDING_MODEL:
        return HashedBaselineEmbedder()
    return SentenceTransformerEmbedder(model=model)


def warm_embedder_model(selection: str) -> str | None:
    model = resolve_embedder_model(selection)
    if model == DEFAULT_EMBEDDING_MODEL:
        return None
    _load_sentence_transformer(model)
    return model


def _iter_features(text: str) -> list[str]:
    tokens = tokenize(text)
    features = list(tokens)
    features.extend(_stem_token(token) for token in tokens if _stem_token(token) != token)
    features.extend(expansion for token in tokens for expansion in _SYNONYM_MAP.get(token, ()))
    features.extend(
        f"{left}__{right}"
        for left, right in zip(tokens, tokens[1:], strict=False)
    )
    return features


def _stem_token(token: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            return token[: -len(suffix)]
    return token


def _feature_bucket_and_sign(feature: str, dimension: int) -> tuple[int, float]:
    digest = hashlib.sha1(feature.encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:8], "big") % dimension
    sign = 1.0 if digest[8] % 2 == 0 else -1.0
    return bucket, sign


def _encode_texts_with_sentence_transformer(texts: list[str], *, model: str) -> list[list[float]]:
    if not texts:
        return []
    try:
        encoder = _load_sentence_transformer(model)
        vectors: list[list[float]] = []
        batch_size = min(_preferred_sentence_transformer_batch_size(model), len(texts))
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            embeddings = encoder.encode(
                batch,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=batch_size,
            )
            vectors.extend([[float(value) for value in row] for row in embeddings.tolist()])
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingError(
            f"Failed to encode text with Hugging Face model repo `{model}`."
        ) from exc

    return vectors


def _preferred_sentence_transformer_batch_size(model: str) -> int:
    normalized = resolve_embedder_model(model)
    if normalized == BGE_M3_EMBEDDING_MODEL:
        return 8
    return 32


@lru_cache(maxsize=2)
def _load_sentence_transformer(model: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise EmbeddingError(
            "sentence-transformers is required for Hugging Face embedding models. "
            "Run `uv sync` to install project dependencies."
        ) from exc

    try:
        return SentenceTransformer(model)
    except Exception as exc:
        raise EmbeddingError(
            f"Failed to load Hugging Face model repo `{model}`. "
            "Check network access and confirm the repo id is valid."
        ) from exc
