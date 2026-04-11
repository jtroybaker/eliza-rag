from __future__ import annotations

import html
import os
from dataclasses import replace
from typing import Any

import streamlit as st

from .answer_generation import AnswerGenerationError, generate_answer
from .config import Settings, get_settings
from .local_runtime import LocalRuntimeError, build_local_runtime_manager
from .models import RetrievalFilters
from .retrieval import (
    BGE_RERANKER_BASE,
    BGE_RERANKER_V2_M3,
    DenseIndexNotReadyError,
    HEURISTIC_RERANKER,
    LexicalIndexNotReadyError,
    analyze_query,
    index_status,
    retrieve,
    warm_retrieval_models,
)
from .storage import fetch_lancedb_archive

RETRIEVAL_MODES = ("targeted_hybrid", "hybrid", "dense", "lexical")
RERANKER_OPTIONS = (BGE_RERANKER_V2_M3, BGE_RERANKER_BASE, HEURISTIC_RERANKER)


def main() -> None:
    st.set_page_config(
        page_title="Editorial Intelligence",
        page_icon="◆",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _apply_chromatic_editorial_theme()
    _init_state()

    base_settings = get_settings()
    provider_options = _available_provider_settings(base_settings)

    st.markdown(
        """
        <div class="app-shell">
          <div class="topbar">
            <div>
              <div class="eyebrow">Portable SEC filings RAG demo</div>
              <h1>SEC Retrieval</h1>
            </div>
            <div class="session-pill">One-page reviewer workflow</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.05, 0.95], gap="large")

    with left_col:
        st.markdown(
            """
            <div class="hero-copy">
              It just reads more.
            </div>
            """,
            unsafe_allow_html=True,
        )
        _render_setup_panel(base_settings)
        selected_settings, mode, rerank, reranker, show_summary = _render_query_controls(provider_options)
        _render_query_form(selected_settings, mode, rerank, reranker, show_summary)

    with right_col:
        _render_results_panel()


def _init_state() -> None:
    st.session_state.setdefault("run_payload", None)
    st.session_state.setdefault("run_error", None)
    st.session_state.setdefault("run_logs", [])
    st.session_state.setdefault("setup_payload", None)
    st.session_state.setdefault("setup_error", None)
    st.session_state.setdefault("runtime_payload", None)
    st.session_state.setdefault("runtime_error", None)


def _available_provider_settings(base: Settings) -> dict[str, Settings]:
    options: dict[str, Settings] = {
        "Local Ollama": replace(
            base,
            llm_provider="local_ollama",
            llm_base_url=base.local_llm_base_url,
            llm_model=base.local_llm_model,
            llm_api_key=None,
        )
    }

    openai_key = os.getenv("ELIZA_RAG_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if openai_key:
        options["Hosted OpenAI"] = replace(
            base,
            llm_provider="openai",
            llm_base_url="https://api.openai.com/v1",
            llm_model="gpt-5-mini",
            llm_api_key=openai_key,
        )

    openrouter_key = os.getenv("ELIZA_RAG_OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        options["Hosted OpenRouter"] = replace(
            base,
            llm_provider="openrouter",
            llm_base_url="https://openrouter.ai/api/v1",
            llm_model="openai/gpt-5-mini",
            llm_api_key=openrouter_key,
        )

    if base.llm_provider == "openai_compatible" and base.llm_base_url:
        options["Configured Compatible API"] = base
    elif base.llm_provider in {"openai", "openrouter"} and base.llm_api_key:
        label = "Hosted OpenAI" if base.llm_provider == "openai" else "Hosted OpenRouter"
        options[label] = base

    return options


def _render_setup_panel(settings: Settings) -> None:
    st.markdown('<div class="section-label">Setup</div>', unsafe_allow_html=True)
    status = index_status(settings)
    lexical_ready = bool(status["lexical"]["table_exists"])
    dense_ready = bool(status["dense"]["table_exists"])

    setup_col, runtime_col = st.columns(2, gap="medium")
    with setup_col:
        st.markdown(
            _metric_card(
                "Environment",
                "Archive ready" if lexical_ready else "Archive missing",
                "Lexical and dense artifacts are checked from the local LanceDB path."
                if lexical_ready and dense_ready
                else "Restore the published archive before running the demo path.",
            ),
            unsafe_allow_html=True,
        )
        if st.button("Restore Archive", use_container_width=True):
            try:
                with st.spinner("Restoring the published LanceDB archive..."):
                    st.session_state.setup_payload = fetch_lancedb_archive(settings)
                    st.session_state.setup_error = None
            except Exception as exc:  # pragma: no cover
                st.session_state.setup_payload = None
                st.session_state.setup_error = str(exc)
            st.rerun()

    with runtime_col:
        manager = build_local_runtime_manager(settings)
        runtime_status = manager.status()
        runtime_label = (
            "Ollama ready"
            if runtime_status.runtime_available
            and runtime_status.server_running
            and runtime_status.model_available
            else "Ollama not ready"
        )
        runtime_detail = (
            f"{runtime_status.model} is available at {runtime_status.base_url}."
            if runtime_status.runtime_available
            and runtime_status.server_running
            and runtime_status.model_available
            else "Check status or prepare the local runtime path."
        )
        st.markdown(
            _metric_card("Local Runtime", runtime_label, runtime_detail),
            unsafe_allow_html=True,
        )
        status_button_col, prepare_button_col = st.columns(2, gap="small")
        with status_button_col:
            if st.button("Check Runtime", use_container_width=True):
                st.session_state.runtime_payload = _runtime_payload(runtime_status)
                st.session_state.runtime_error = None
                st.rerun()
        with prepare_button_col:
            if st.button("Prepare Runtime", use_container_width=True):
                try:
                    with st.spinner("Preparing Ollama and warming retrieval models..."):
                        prepared = manager.prepare(pull=True)
                        retrieval_warmup = warm_retrieval_models(settings)
                    st.session_state.runtime_payload = {
                        **_runtime_payload(prepared),
                        "retrieval_warmup": retrieval_warmup,
                    }
                    st.session_state.runtime_error = None
                except (LocalRuntimeError, RuntimeError) as exc:
                    st.session_state.runtime_payload = None
                    st.session_state.runtime_error = str(exc)
                st.rerun()

    if st.session_state.setup_error:
        st.error(st.session_state.setup_error)
    elif st.session_state.setup_payload:
        st.success("Archive restored.")
        with st.expander("Archive details", expanded=False):
            st.json(st.session_state.setup_payload)

    if st.session_state.runtime_error:
        st.error(st.session_state.runtime_error)
    elif st.session_state.runtime_payload:
        st.success("Runtime status refreshed.")
        with st.expander("Runtime details", expanded=False):
            st.json(st.session_state.runtime_payload)


def _render_query_controls(
    provider_options: dict[str, Settings],
) -> tuple[Settings, str, bool, str, bool]:
    st.markdown('<div class="section-label">Ask</div>', unsafe_allow_html=True)
    provider_label = st.radio(
        "Provider",
        tuple(provider_options.keys()),
        horizontal=True,
        label_visibility="collapsed",
    )
    selected_settings = provider_options[provider_label]

    mode_col, rerank_col = st.columns(2, gap="medium")
    with mode_col:
        mode = st.selectbox(
            "Retrieval mode",
            RETRIEVAL_MODES,
            index=0,
            help="The recommended reviewer path stays at targeted_hybrid.",
        )
    with rerank_col:
        rerank = st.toggle(
            "Enable reranking",
            value=True,
            help="The recommended reviewer path keeps reranking enabled.",
        )

    with st.expander("Advanced options", expanded=False):
        reranker = st.selectbox(
            "Reranker",
            RERANKER_OPTIONS,
            index=0,
            disabled=not rerank,
        )
        show_summary = st.toggle(
            "Show summary",
            value=False,
            help="Display the model-generated executive summary alongside the grounded answer.",
        )
        st.caption(
            f"Answer backend: `{selected_settings.llm_provider}` using model `{selected_settings.llm_model}`"
        )

    return selected_settings, mode, rerank, reranker, show_summary


def _render_query_form(
    settings: Settings,
    mode: str,
    rerank: bool,
    reranker: str,
    show_summary: bool,
) -> None:
    with st.form("query-form", clear_on_submit=False):
        question = st.text_area(
            "Your thesis",
            placeholder="What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?",
            height=170,
            label_visibility="collapsed",
        )
        run_mode = st.radio(
            "Run mode",
            ("Answer", "Search"),
            horizontal=True,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button(
            "Synthesize Results" if run_mode == "Answer" else "Search Evidence",
            use_container_width=True,
            type="primary",
        )

    if not submitted:
        return

    if not question.strip():
        st.session_state.run_error = "Enter a question before running the demo."
        st.session_state.run_payload = None
        st.session_state.run_logs = []
        st.rerun()

    logs: list[str] = []
    status_placeholder = st.empty()

    def _progress(message: str) -> None:
        logs.append(message)
        status_placeholder.markdown(_status_banner(message), unsafe_allow_html=True)

    filters = RetrievalFilters()
    try:
        with st.spinner("Running the RAG flow..."):
            structured_query = analyze_query(question, filters=filters, settings=settings).to_dict()
            if run_mode == "Answer":
                response = generate_answer(
                    settings,
                    question,
                    mode=mode,
                    filters=filters,
                    enable_rerank=rerank,
                    reranker=reranker if rerank else None,
                    progress_callback=_progress,
                )
                response_payload = response.to_dict()
                if not show_summary:
                    response_payload.pop("summary", None)
                payload = {
                    "kind": "answer",
                    "provider": settings.llm_provider,
                    "model": settings.llm_model,
                    "retrieval_mode": mode,
                    "show_summary": show_summary,
                    "structured_query": structured_query,
                    "index_status": index_status(settings),
                    "response": response_payload,
                }
            else:
                _progress("Analyzing query and retrieving evidence...")
                results = retrieve(
                    settings,
                    question,
                    mode=mode,
                    filters=filters,
                    enable_rerank=rerank,
                    reranker=reranker if rerank else None,
                )
                payload = {
                    "kind": "search",
                    "provider": settings.llm_provider,
                    "model": settings.llm_model,
                    "retrieval_mode": mode,
                    "structured_query": structured_query,
                    "index_status": index_status(settings),
                    "results": [result.to_dict() for result in results],
                }
        st.session_state.run_payload = payload
        st.session_state.run_error = None
        st.session_state.run_logs = logs
    except (
        AnswerGenerationError,
        DenseIndexNotReadyError,
        LexicalIndexNotReadyError,
        LocalRuntimeError,
        RuntimeError,
        ValueError,
    ) as exc:
        st.session_state.run_payload = None
        st.session_state.run_error = str(exc)
        st.session_state.run_logs = logs
    st.rerun()


def _render_results_panel() -> None:
    st.markdown(
        """
        <div class="results-header">
          <div>
            <div class="section-label">Inspect</div>
            <h2>Status &amp; Results</h2>
          </div>
          <div class="session-pill">Session active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.run_error:
        st.error(st.session_state.run_error)
    elif st.session_state.run_logs:
        st.markdown(_status_banner(st.session_state.run_logs[-1]), unsafe_allow_html=True)

    payload = st.session_state.run_payload
    if payload is None:
        st.markdown(
            """
            <div class="empty-state">
              <h3>Ready for a first pass.</h3>
              <p>
                Restore the archive if needed, choose a provider path, and run either the answer
                flow or retrieval-only search.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    with st.expander("Run metadata", expanded=False):
        st.json(
            {
                "provider": payload["provider"],
                "model": payload["model"],
                "retrieval_mode": payload["retrieval_mode"],
                "structured_query": payload["structured_query"],
                "index_status": payload["index_status"],
                "progress": st.session_state.run_logs,
            }
        )

    if payload["kind"] == "answer":
        _render_answer_payload(payload["response"], show_summary=bool(payload.get("show_summary")))
    else:
        _render_search_payload(payload["results"])


def _render_answer_payload(response: dict[str, Any], *, show_summary: bool) -> None:
    st.markdown(
        """
        <div class="result-prose">
          <h3>Grounded answer</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="result-card answer-card">
          <div class="result-body">{_paragraphs(response["answer"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    summary = response.get("summary")
    findings = response.get("findings") or []
    uncertainty = response.get("uncertainty")
    if show_summary and summary:
        st.markdown(
            f"""
            <div class="result-card">
              <div class="card-label">Summary</div>
              <div class="result-body"><p>{html.escape(summary)}</p></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if findings:
        finding_items = "".join(
            f"<li>{html.escape(item['statement'])}</li>"
            for item in findings
            if item.get("statement")
        )
        st.markdown(
            f"""
            <div class="result-card">
              <div class="card-label">Findings</div>
              <ul class="finding-list">{finding_items}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if uncertainty:
        st.markdown(
            f"""
            <div class="result-card muted-card">
              <div class="card-label">Uncertainty</div>
              <div class="result-body"><p>{html.escape(uncertainty)}</p></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    retrieval_results = response.get("retrieval_results") or []
    citations = response.get("citations") or []
    if citations:
        st.markdown('<div class="section-label">Evidence</div>', unsafe_allow_html=True)
        retrieval_by_chunk_id = {
            str(result.get("chunk_id")): result
            for result in retrieval_results
            if result.get("chunk_id")
        }
        for citation in citations:
            _render_citation_expander(citation, retrieval_by_chunk_id.get(str(citation.get("chunk_id"))))
    elif retrieval_results:
        st.markdown('<div class="section-label">Retrieved chunks</div>', unsafe_allow_html=True)
        _render_result_expanders(retrieval_results)


def _render_search_payload(results: list[dict[str, Any]]) -> None:
    if not results:
        st.warning("No retrieval results were returned for this query.")
        return
    st.markdown('<div class="section-label">Retrieved chunks</div>', unsafe_allow_html=True)
    _render_result_expanders(results)


def _render_result_expanders(results: list[dict[str, Any]]) -> None:
    for result in results:
        company = result.get("company_name") or result.get("ticker") or "Unknown issuer"
        section = _evidence_section_label(result)
        score_parts = []
        if result.get("raw_score") is not None:
            score_parts.append(f"score {result['raw_score']:.3f}")
        if result.get("rerank_score") is not None:
            score_parts.append(f"rerank {result['rerank_score']:.3f}")
        caption = " • ".join(score_parts) if score_parts else "ranked result"
        with st.expander(f"{company} • {section} • {caption}", expanded=False):
            st.caption(
                f"{result.get('form_type', 'Unknown form')} • {result.get('filing_date', 'Unknown date')} • {result.get('chunk_id', 'unknown chunk')}"
            )
            st.write(result.get("text", ""))


def _metric_card(title: str, value: str, detail: str) -> str:
    return f"""
    <div class="metric-card">
      <div class="card-label">{html.escape(title)}</div>
      <div class="metric-value">{html.escape(value)}</div>
      <div class="metric-detail">{html.escape(detail)}</div>
    </div>
    """


def _citation_card(citation: dict[str, Any]) -> str:
    label = html.escape(citation.get("citation_id") or "Source")
    company = html.escape(citation.get("company_name") or citation.get("ticker") or "Unknown issuer")
    section = html.escape(_evidence_section_label(citation))
    form_type = html.escape(citation.get("form_type") or "Unknown form")
    filing_date = html.escape(citation.get("filing_date") or "Unknown date")
    chunk_id = html.escape(citation.get("chunk_id") or "unknown chunk")
    return f"""
    <div class="result-card citation-card">
      <div class="citation-row">
        <div class="card-label">[{label}]</div>
        <div class="chunk-id">{chunk_id}</div>
      </div>
      <div class="citation-title">{company}</div>
      <div class="metric-detail">{form_type} • {filing_date} • {section}</div>
    </div>
    """


def _render_citation_expander(citation: dict[str, Any], result: dict[str, Any] | None) -> None:
    citation_id = str(citation.get("citation_id") or "Source")
    company = citation.get("company_name") or citation.get("ticker") or "Unknown issuer"
    section = _evidence_section_label(result or citation)
    detail_parts = []
    if result and result.get("rank") is not None:
        detail_parts.append(f"rank {result['rank']}")
    if result and result.get("raw_score") is not None:
        detail_parts.append(f"score {result['raw_score']:.3f}")
    if result and result.get("rerank_score") is not None:
        detail_parts.append(f"rerank {result['rerank_score']:.3f}")
    caption = f" • {' • '.join(detail_parts)}" if detail_parts else ""
    header = f"[{citation_id}] {company} • {section}{caption}"

    with st.expander(header, expanded=False):
        st.markdown(_citation_card(citation), unsafe_allow_html=True)

        if result and result.get("text"):
            st.markdown("**Chunk text**")
            st.write(result["text"])
        else:
            st.caption("Chunk text unavailable for this citation.")

        metadata = dict(citation)
        if result:
            for key in (
                "chunk_index",
                "section_path",
                "fiscal_period",
                "source_path",
                "retrieval_mode",
                "source_retrieval_mode",
                "rank",
                "raw_score",
                "rerank_score",
            ):
                if result.get(key) is not None and metadata.get(key) is None:
                    metadata[key] = result[key]

        st.markdown("**Chunk metadata**")
        st.json(metadata)


def _evidence_section_label(payload: dict[str, Any]) -> str:
    section = _clean_evidence_value(payload.get("section"))
    section_path = _clean_evidence_value(payload.get("section_path"))
    form_type = _clean_evidence_value(payload.get("form_type"))
    chunk_index = payload.get("chunk_index")

    if section and section_path and section.lower() != section_path.lower():
        return f"{section} ({section_path})"
    if section_path:
        return section_path
    if section:
        return section
    if form_type and isinstance(chunk_index, int):
        return f"{form_type} chunk {chunk_index + 1}"
    if form_type:
        return f"{form_type} excerpt"
    if isinstance(chunk_index, int):
        return f"Chunk {chunk_index + 1}"
    return "Filing excerpt"


def _clean_evidence_value(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    if stripped.lower() == "unknown section":
        return None
    return stripped


def _paragraphs(text: str) -> str:
    parts = [segment.strip() for segment in text.split("\n") if segment.strip()]
    if not parts:
        return "<p>No answer text returned.</p>"
    return "".join(f"<p>{html.escape(part)}</p>" for part in parts)


def _runtime_payload(status: Any) -> dict[str, Any]:
    return {
        "runtime": status.runtime,
        "command": status.command,
        "base_url": status.base_url,
        "model": status.model,
        "runtime_available": status.runtime_available,
        "server_running": status.server_running,
        "model_available": status.model_available,
    }


def _status_banner(message: str) -> str:
    return f"""
    <div class="status-banner">
      <div class="status-dot"></div>
      <div>
        <div class="card-label">Pipeline status</div>
        <div class="status-message">{html.escape(message)}</div>
      </div>
    </div>
    """


def _apply_chromatic_editorial_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300..800;1,6..72,300..800&family=Manrope:wght@300;400;500;600;700;800&display=swap');

        :root {
          --bg: #111416;
          --surface-low: #191c1e;
          --surface: #1d2022;
          --surface-high: #272a2c;
          --surface-highest: #323537;
          --surface-lowest: #0c0f11;
          --text: #e1e2e5;
          --muted: #b69798;
          --muted-soft: #8f7a7b;
          --rose: #e11d48;
          --rose-soft: #ffb3b6;
          --success: #34d399;
        }

        html, body, [class*="css"]  {
          font-family: "Manrope", sans-serif;
        }

        .stApp {
          background:
            radial-gradient(circle at top left, rgba(225, 29, 72, 0.09), transparent 26rem),
            linear-gradient(180deg, rgba(255, 179, 182, 0.04), transparent 14rem),
            var(--bg);
          color: var(--text);
        }

        [data-testid="stHeader"] {
          background: transparent;
        }

        [data-testid="stToolbar"] {
          right: 1rem;
        }

        .block-container {
          max-width: 1380px;
          padding-top: 2rem;
          padding-bottom: 3rem;
        }

        h1, h2, h3 {
          font-family: "Newsreader", serif;
          font-weight: 400;
          letter-spacing: -0.02em;
          color: var(--text);
        }

        .app-shell {
          margin-bottom: 1.5rem;
        }

        .topbar, .results-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 1rem;
          margin-bottom: 1rem;
        }

        .topbar h1 {
          font-size: clamp(3rem, 5vw, 4.8rem);
          font-style: italic;
          line-height: 0.95;
          margin: 0;
        }

        .hero-copy {
          max-width: 42rem;
          font-size: 1.1rem;
          line-height: 1.75;
          color: rgba(225, 226, 229, 0.72);
          margin: 0 0 1.75rem 0;
        }

        .eyebrow, .section-label, .card-label {
          font-size: 0.72rem;
          line-height: 1;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: var(--muted);
        }

        .session-pill {
          background: rgba(225, 29, 72, 0.10);
          border: 1px solid rgba(255, 179, 182, 0.15);
          color: var(--rose-soft);
          border-radius: 999px;
          padding: 0.45rem 0.85rem;
          font-size: 0.7rem;
          line-height: 1;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          white-space: nowrap;
        }

        .metric-card, .result-card, .empty-state {
          background: linear-gradient(180deg, rgba(39, 42, 44, 0.88), rgba(25, 28, 30, 0.95));
          border-radius: 1.5rem;
          padding: 1.3rem 1.35rem;
          margin-bottom: 1rem;
          box-shadow: 0 20px 50px rgba(0, 0, 0, 0.20);
        }

        .metric-card {
          min-height: 10rem;
          background: linear-gradient(180deg, rgba(18, 20, 22, 0.95), rgba(12, 15, 17, 0.95));
        }

        .metric-value {
          color: var(--text);
          font-size: 1.2rem;
          font-weight: 700;
          margin-top: 1rem;
          margin-bottom: 0.55rem;
        }

        .metric-detail, .status-message {
          color: rgba(225, 226, 229, 0.68);
          line-height: 1.6;
          font-size: 0.95rem;
        }

        .result-prose h3 {
          font-size: 0.82rem;
          font-weight: 700;
          letter-spacing: 0.18em;
          line-height: 1.3;
          margin: 0 0 0.85rem 0;
          text-transform: uppercase;
          color: rgba(225, 226, 229, 0.58);
        }

        .result-body {
          color: rgba(225, 226, 229, 0.92);
          font-size: 1.08rem;
          line-height: 1.85;
        }

        .result-body p {
          margin-top: 0;
          margin-bottom: 1.1rem;
        }

        .answer-card {
          background: rgba(17, 20, 22, 0.78);
          backdrop-filter: blur(20px);
        }

        .muted-card {
          background: rgba(29, 32, 34, 0.7);
        }

        .citation-card {
          border-left: 2px solid rgba(255, 179, 182, 0.8);
        }

        .citation-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          margin-bottom: 0.5rem;
        }

        .citation-title {
          font-family: "Newsreader", serif;
          font-size: 1.35rem;
          margin-bottom: 0.3rem;
        }

        .chunk-id {
          color: rgba(225, 226, 229, 0.55);
          font-family: monospace;
          font-size: 0.75rem;
        }

        .finding-list {
          color: rgba(225, 226, 229, 0.92);
          padding-left: 1.15rem;
          margin-bottom: 0;
          line-height: 1.7;
        }

        .status-banner {
          display: flex;
          gap: 0.9rem;
          align-items: flex-start;
          background: rgba(29, 32, 34, 0.72);
          backdrop-filter: blur(20px);
          border-left: 3px solid var(--rose-soft);
          border-radius: 1.35rem;
          padding: 1rem 1.1rem;
          margin-bottom: 1.2rem;
        }

        .status-dot {
          width: 0.65rem;
          height: 0.65rem;
          margin-top: 0.2rem;
          border-radius: 999px;
          background: linear-gradient(180deg, var(--rose-soft), var(--rose));
          box-shadow: 0 0 18px rgba(225, 29, 72, 0.45);
          flex: 0 0 auto;
        }

        .empty-state h3 {
          font-size: 2rem;
          margin-top: 0;
          margin-bottom: 0.75rem;
        }

        .empty-state p {
          color: rgba(225, 226, 229, 0.68);
          line-height: 1.7;
          margin-bottom: 0;
          max-width: 36rem;
        }

        .stTextArea textarea {
          background: var(--surface-high);
          color: var(--text);
          border: 1px solid transparent;
          border-radius: 1.5rem;
          font-size: 1.08rem;
          line-height: 1.7;
          padding: 1.15rem 1.2rem;
        }

        .stTextArea textarea:focus {
          border-color: rgba(255, 179, 182, 0.55);
          box-shadow: 0 0 0 1px rgba(255, 179, 182, 0.25);
        }

        .stTextArea textarea::placeholder {
          color: rgba(225, 226, 229, 0.28);
        }

        .stRadio > label, .stSelectbox > label, .stToggle > label {
          color: var(--muted);
          font-size: 0.72rem;
          letter-spacing: 0.16em;
          text-transform: uppercase;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
          background: rgba(12, 15, 17, 0.95);
          border-radius: 1rem;
          border: 1px solid rgba(255, 179, 182, 0.06);
        }

        .stButton > button, .stFormSubmitButton > button {
          border-radius: 1.35rem;
          border: none;
          min-height: 3rem;
          font-weight: 700;
          letter-spacing: 0.01em;
          transition: transform 160ms ease, box-shadow 160ms ease, opacity 160ms ease;
        }

        .stButton > button:hover, .stFormSubmitButton > button:hover {
          transform: translateY(-1px);
          box-shadow: 0 16px 30px rgba(225, 29, 72, 0.15);
        }

        .stFormSubmitButton > button[kind="primary"] {
          background: linear-gradient(135deg, #ff355f, #e11d48);
          color: #fffaf9;
          font-family: "Newsreader", serif;
          font-size: 1.7rem;
          font-style: italic;
          min-height: 4.25rem;
        }

        .stToggle [data-baseweb="checkbox"] > div {
          background-color: var(--surface-lowest);
        }

        .stExpander {
          background: rgba(25, 28, 30, 0.72);
          border-radius: 1.1rem;
          border: 1px solid rgba(255, 179, 182, 0.06);
        }

        .stAlert {
          border-radius: 1rem;
        }

        @media (max-width: 1100px) {
          .topbar, .results-header {
            flex-direction: column;
          }

          .topbar h1 {
            font-size: 3rem;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
