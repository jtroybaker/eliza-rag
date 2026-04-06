from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib import error, request
from urllib.parse import urlsplit

from .config import Settings
from .interfaces import AnswerBackend
from .local_runtime import LocalRuntimeError, build_local_runtime_manager
from .models import AnswerCitation, AnswerFinding, AnswerResponse, RetrievalFilters, RetrievalResult
from .retrieval import (
    DenseIndexNotReadyError,
    LexicalIndexNotReadyError,
    RetrievalMode,
    retrieve,
)


class AnswerGenerationError(RuntimeError):
    """Raised when the final answer generation step cannot complete."""


@dataclass(slots=True)
class PromptPackage:
    prompt: str
    citations: list[AnswerCitation]
    prompt_path: Path


INLINE_CITATION_PATTERN = re.compile(r"\[(C\d+)\]")
BRACKETED_CITATION_GROUP_PATTERN = re.compile(r"\[(C\d+(?:\s*,\s*C\d+)+)\]")
PARENTHETICAL_CITATION_GROUP_PATTERN = re.compile(r"\((C\d+(?:\s*,\s*C\d+)*)\)")


class OpenAICompatibleResponsesClient:
    """Minimal OpenAI-compatible Responses API client for the final single-call answer path."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        base_url: str,
        provider_label: str,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._provider_label = provider_label
        self._extra_headers = extra_headers or {}

    @property
    def model(self) -> str:
        return self._model

    def generate(self, prompt: str) -> str:
        body = json.dumps(
            {
                "model": self._model,
                "input": prompt,
            }
        ).encode("utf-8")
        http_request = request.Request(
            f"{self._base_url}/responses",
            data=body,
            headers=self._build_headers(),
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise AnswerGenerationError(
                f"{self._provider_label} request failed: {detail}"
            ) from exc
        except error.URLError as exc:
            raise AnswerGenerationError(
                f"{self._provider_label} endpoint is unreachable: {exc.reason}"
            ) from exc

        extracted_text = _extract_output_text(payload)
        if extracted_text is not None:
            return extracted_text

        raise AnswerGenerationError(
            f"{self._provider_label} returned an incompatible response shape: missing text output."
        )

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            **self._extra_headers,
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers


class LocalOllamaGenerateClient:
    """Native Ollama client for local runs, using explicit JSON mode."""

    def __init__(self, *, model: str, base_url: str) -> None:
        self._model = model
        parsed = urlsplit(base_url)
        self._base_url = f"{parsed.scheme}://{parsed.netloc}"

    @property
    def model(self) -> str:
        return self._model

    def generate(self, prompt: str) -> str:
        body = json.dumps(
            {
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            }
        ).encode("utf-8")
        http_request = request.Request(
            f"{self._base_url}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise AnswerGenerationError(
                f"Repo-managed local Ollama backend request failed: {detail}"
            ) from exc
        except error.URLError as exc:
            raise AnswerGenerationError(
                f"Repo-managed local Ollama backend endpoint is unreachable: {exc.reason}"
            ) from exc

        response_text = payload.get("response")
        if isinstance(response_text, str) and response_text.strip():
            return response_text.strip()

        raise AnswerGenerationError(
            "Repo-managed local Ollama backend returned an incompatible response shape: missing `response`."
        )


def _extract_output_text(payload: dict[str, object]) -> str | None:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = payload.get("output")
    if isinstance(output, list):
        content_parts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            for key in ("content",):
                maybe_content = item.get(key)
                _append_content_text(content_parts, maybe_content)
        if content_parts:
            return "\n".join(content_parts)

    message = payload.get("message")
    if isinstance(message, dict):
        content_parts: list[str] = []
        _append_content_text(content_parts, message.get("content"))
        if content_parts:
            return "\n".join(content_parts)

    return None


def _append_content_text(parts: list[str], content: object) -> None:
    if isinstance(content, str):
        stripped = content.strip()
        if stripped:
            parts.append(stripped)
        return
    if not isinstance(content, list):
        return
    for block in content:
        if not isinstance(block, dict):
            continue
        text = block.get("text")
        if isinstance(text, str):
            stripped = text.strip()
            if stripped:
                parts.append(stripped)


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    provider: str
    base_url: str
    requires_api_key: bool
    provider_label: str
    extra_headers: dict[str, str]


def resolve_provider_config(settings: Settings) -> ProviderConfig:
    provider = settings.llm_provider.strip().lower()
    if provider == "openai":
        return ProviderConfig(
            provider=provider,
            base_url=settings.llm_base_url,
            requires_api_key=True,
            provider_label="Hosted OpenAI backend",
            extra_headers={},
        )
    if provider == "openrouter":
        return ProviderConfig(
            provider=provider,
            base_url=settings.llm_base_url,
            requires_api_key=True,
            provider_label="Hosted OpenRouter backend",
            extra_headers={},
        )
    if provider == "openai_compatible":
        return ProviderConfig(
            provider=provider,
            base_url=settings.llm_base_url,
            requires_api_key=False,
            provider_label="Configured OpenAI-compatible backend",
            extra_headers={},
        )
    if provider == "local_ollama":
        return ProviderConfig(
            provider=provider,
            base_url=settings.llm_base_url,
            requires_api_key=False,
            provider_label="Repo-managed local Ollama backend",
            extra_headers={},
        )
    raise AnswerGenerationError(
        "Unsupported LLM provider. Expected one of: openai, openrouter, openai_compatible, local_ollama."
    )


def build_answer_backend_client(settings: Settings) -> AnswerBackend:
    provider_config = resolve_provider_config(settings)
    if provider_config.requires_api_key and not settings.llm_api_key:
        raise AnswerGenerationError(
            f"ELIZA_RAG_LLM_API_KEY is required for hosted provider `{provider_config.provider}`."
        )
    if provider_config.provider == "local_ollama":
        try:
            build_local_runtime_manager(settings).ensure_ready()
        except LocalRuntimeError as exc:
            raise AnswerGenerationError(str(exc)) from exc
        return LocalOllamaGenerateClient(
            model=settings.llm_model,
            base_url=provider_config.base_url,
        )
    return OpenAICompatibleResponsesClient(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=provider_config.base_url,
        provider_label=provider_config.provider_label,
        extra_headers=provider_config.extra_headers,
    )


def generate_answer(
    settings: Settings,
    question: str,
    *,
    mode: RetrievalMode = "hybrid",
    top_k: int | None = None,
    filters: RetrievalFilters | None = None,
    phrase_query: bool = False,
    enable_rerank: bool | None = None,
    reranker: str | None = None,
    rerank_candidate_pool: int | None = None,
    client: AnswerBackend | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> AnswerResponse:
    if progress_callback:
        progress_callback("Analyzing query and retrieving evidence...")
    try:
        retrieval_results = retrieve(
            settings,
            question,
            mode=mode,
            top_k=top_k or settings.answer_top_k,
            filters=filters,
            phrase_query=phrase_query,
            enable_rerank=enable_rerank,
            reranker=reranker,
            rerank_candidate_pool=rerank_candidate_pool,
        )
    except (DenseIndexNotReadyError, LexicalIndexNotReadyError):
        raise

    if not retrieval_results:
        raise AnswerGenerationError("No retrieval results were returned for the supplied question.")

    if progress_callback:
        progress_callback("Building grounded prompt...")
    prompt_package = build_prompt_package(settings, question, retrieval_results)
    if progress_callback:
        progress_callback(
            f"Calling {settings.llm_provider} backend with model `{settings.llm_model}`..."
        )
    active_client = client or build_answer_backend_client(settings)
    raw_model_response = active_client.generate(prompt_package.prompt)
    if progress_callback:
        progress_callback("Validating model response and citations...")
    parsed_response = parse_model_response(raw_model_response, prompt_package.citations)

    return AnswerResponse(
        question=question,
        answer=parsed_response["answer"],
        summary=parsed_response["summary"],
        findings=parsed_response["findings"],
        uncertainty=parsed_response["uncertainty"],
        citations=prompt_package.citations,
        retrieval_mode=mode,
        prompt_path=str(prompt_package.prompt_path),
        prompt_preview=prompt_package.prompt[:500],
        prompt_characters=len(prompt_package.prompt),
        retrieval_results=retrieval_results,
        raw_model_response=raw_model_response,
        model=active_client.model,
    )


def build_prompt_package(
    settings: Settings,
    question: str,
    retrieval_results: list[RetrievalResult],
) -> PromptPackage:
    template = settings.final_prompt_template_path.read_text(encoding="utf-8").strip()
    context_lines: list[str] = []
    citations: list[AnswerCitation] = []

    for index, result in enumerate(retrieval_results, start=1):
        citation_id = f"C{index}"
        citations.append(
            AnswerCitation(
                citation_id=citation_id,
                chunk_id=result.chunk_id,
                filing_id=result.filing_id,
                ticker=result.ticker,
                company_name=result.company_name,
                form_type=result.form_type,
                filing_date=result.filing_date,
                section=result.section,
                source_path=result.source_path,
            )
        )
        header = (
            f"[{citation_id}] ticker={result.ticker} "
            f"company={result.company_name or 'unknown'} "
            f"form_type={result.form_type} "
            f"filing_date={result.filing_date} "
            f"filing_id={result.filing_id} "
            f"chunk_id={result.chunk_id} "
            f"section={result.section or 'unknown'}"
        )
        context_lines.append(f"{header}\n{result.text.strip()}")

    prompt = (
        template.replace("{question}", question.strip()).replace(
            "{context}",
            "\n\n".join(context_lines),
        )
    )
    return PromptPackage(
        prompt=prompt,
        citations=citations,
        prompt_path=settings.final_prompt_template_path,
    )


def parse_model_response(
    raw_model_response: str,
    citations: list[AnswerCitation],
) -> dict[str, object]:
    try:
        payload = _parse_json_object_response(raw_model_response)
    except json.JSONDecodeError as exc:
        raise AnswerGenerationError(
            "Model response was not valid JSON. The final prompt expects a strict JSON object."
        ) from exc

    if not isinstance(payload, dict):
        raise AnswerGenerationError("Model response JSON must be an object.")

    citation_ids = {citation.citation_id for citation in citations}
    findings_payload = payload.get("findings")
    if not isinstance(findings_payload, list) or not findings_payload:
        raise AnswerGenerationError("Model response must include a non-empty `findings` list.")

    findings: list[AnswerFinding] = []
    for item in findings_payload:
        if not isinstance(item, dict):
            raise AnswerGenerationError("Each finding must be a JSON object.")
        statement = item.get("statement")
        finding_citations = item.get("citations")
        if not isinstance(statement, str) or not statement.strip():
            raise AnswerGenerationError("Each finding must include a non-empty `statement`.")
        if not isinstance(finding_citations, list) or not finding_citations:
            raise AnswerGenerationError("Each finding must include at least one citation id.")
        normalized_citations = [str(value) for value in finding_citations]
        known_citations = [citation_id for citation_id in normalized_citations if citation_id in citation_ids]
        if not known_citations:
            continue
        findings.append(
            AnswerFinding(
                statement=statement.strip(),
                citations=known_citations,
            )
        )

    answer = payload.get("answer")
    summary = payload.get("summary")
    uncertainty = payload.get("uncertainty")
    if not isinstance(answer, str) or not answer.strip():
        raise AnswerGenerationError("Model response must include a non-empty `answer`.")
    if not isinstance(summary, str) or not summary.strip():
        raise AnswerGenerationError("Model response must include a non-empty `summary`.")
    if not isinstance(uncertainty, str):
        raise AnswerGenerationError("Model response must include an `uncertainty` string.")

    normalized_answer = _normalize_inline_answer_citations(answer.strip())
    answer_citations = INLINE_CITATION_PATTERN.findall(normalized_answer)
    known_answer_citations = [citation_id for citation_id in answer_citations if citation_id in citation_ids]
    if not known_answer_citations:
        normalized_answer = _strip_unknown_inline_citations(normalized_answer, citation_ids)
        finding_citation_ids: list[str] = []
        for finding in findings:
            for citation_id in finding.citations:
                if citation_id not in finding_citation_ids:
                    finding_citation_ids.append(citation_id)
        if finding_citation_ids:
            normalized_answer = normalized_answer.rstrip() + " " + " ".join(
                f"[{citation_id}]" for citation_id in finding_citation_ids
            )
            answer_citations = finding_citation_ids
        else:
            raise AnswerGenerationError(
                "Model response `answer` must include inline citation ids such as [C1]."
            )
    elif len(known_answer_citations) != len(answer_citations):
        normalized_answer = _strip_unknown_inline_citations(normalized_answer, citation_ids)

    if not findings:
        raise AnswerGenerationError("Model response must include at least one finding with known citation ids.")

    return {
        "answer": normalized_answer,
        "summary": summary.strip(),
        "findings": findings,
        "uncertainty": uncertainty.strip(),
    }


def _parse_json_object_response(raw_model_response: str) -> dict[str, object]:
    normalized = raw_model_response.strip()
    candidates = [normalized]

    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", normalized, re.DOTALL | re.IGNORECASE)
    if fenced_match:
        candidates.append(fenced_match.group(1).strip())

    decoder = json.JSONDecoder()
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            start = candidate.find("{")
            if start < 0:
                continue
            try:
                payload, _ = decoder.raw_decode(candidate[start:])
            except json.JSONDecodeError:
                continue
        if isinstance(payload, dict):
            return payload
        raise AnswerGenerationError("Model response JSON must be an object.")

    raise json.JSONDecodeError("No JSON object found", normalized, 0)


def _normalize_inline_answer_citations(answer: str) -> str:
    def _replace_group(match: re.Match[str]) -> str:
        citation_ids = [part.strip() for part in match.group(1).split(",")]
        return " " + " ".join(f"[{citation_id}]" for citation_id in citation_ids)

    normalized = BRACKETED_CITATION_GROUP_PATTERN.sub(_replace_group, answer)
    normalized = PARENTHETICAL_CITATION_GROUP_PATTERN.sub(_replace_group, normalized)
    normalized = re.sub(r"\s+([.,;:])", r"\1", normalized)
    return re.sub(r"\s{2,}", " ", normalized).strip()


def _strip_unknown_inline_citations(answer: str, citation_ids: set[str]) -> str:
    def _replace(match: re.Match[str]) -> str:
        citation_id = match.group(1)
        return match.group(0) if citation_id in citation_ids else ""

    normalized = re.sub(r"\[(C\d+)\]", _replace, answer)
    normalized = re.sub(r"\s+([.,;:])", r"\1", normalized)
    return re.sub(r"\s{2,}", " ", normalized).strip()
