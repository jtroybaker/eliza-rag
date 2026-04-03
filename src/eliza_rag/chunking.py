from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from .config import Settings
from .corpus import build_chunk_record
from .models import ChunkRecord, FilingRecord

HEADER_SEPARATOR_RE = re.compile(r"\n=+\n", re.MULTILINE)
BODY_START_MARKERS = (
    "UNITED STATESSECURITIES AND EXCHANGE COMMISSION",
    "UNITED STATES SECURITIES AND EXCHANGE COMMISSION",
    "FORM 10-K",
    "FORM 10-Q",
)
SECTION_BREAK_PATTERNS = (
    re.compile(r"(?<!\n)(TABLE OF CONTENTS)", re.IGNORECASE),
    re.compile(r"(?<!\n)(PART\s+[IVX]+\b)", re.IGNORECASE),
    re.compile(r"(?<!\n)(Item\s+\d+[A-Z]?\.)", re.IGNORECASE),
    re.compile(r"(?<!\n)(SIGNATURES\b)", re.IGNORECASE),
)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")
PART_RE = re.compile(r"^(PART\s+[IVX]+\b.*)$", re.IGNORECASE)
ITEM_RE = re.compile(r"^(Item\s+\d+[A-Z]?\.\s*.*)$", re.IGNORECASE)


@dataclass(slots=True)
class Paragraph:
    text: str
    section: str | None
    section_path: str | None
    token_count: int


def estimate_token_count(text: str) -> int:
    words = len(text.split())
    return max(1, math.ceil(words * 1.3))


def extract_filing_body(raw_text: str) -> str:
    match = HEADER_SEPARATOR_RE.search(raw_text)
    body = raw_text[match.end() :] if match else raw_text

    marker_positions = [body.find(marker) for marker in BODY_START_MARKERS if body.find(marker) != -1]
    if marker_positions:
        body = body[min(marker_positions) :]

    return body.strip()


def normalize_filing_text(raw_text: str) -> str:
    text = extract_filing_body(raw_text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")

    for pattern in SECTION_BREAK_PATTERNS:
        text = pattern.sub(r"\n\1", text)

    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_long_text(text: str, max_tokens: int) -> list[str]:
    if estimate_token_count(text) <= max_tokens:
        return [text.strip()]

    sentences = [segment.strip() for segment in SENTENCE_SPLIT_RE.split(text) if segment.strip()]
    if len(sentences) <= 1:
        words = text.split()
        window = max(1, int(max_tokens / 1.3))
        return [" ".join(words[index : index + window]) for index in range(0, len(words), window)]

    parts: list[str] = []
    current: list[str] = []

    for sentence in sentences:
        candidate = "\n".join(current + [sentence]) if current else sentence
        if current and estimate_token_count(candidate) > max_tokens:
            parts.append(" ".join(current).strip())
            current = [sentence]
            continue
        current.append(sentence)

    if current:
        parts.append(" ".join(current).strip())

    return [part for part in parts if part]


def detect_section_heading(text: str) -> tuple[str | None, str | None]:
    stripped = text.strip()
    part_match = PART_RE.match(stripped)
    if part_match:
        heading = part_match.group(1).strip()
        return heading, heading

    item_match = ITEM_RE.match(stripped)
    if item_match:
        heading = item_match.group(1).strip()
        return heading, heading

    return None, None


def extract_paragraphs(raw_text: str, *, max_tokens: int) -> list[Paragraph]:
    normalized_text = normalize_filing_text(raw_text)
    blocks = [block.strip() for block in re.split(r"\n\s*\n", normalized_text) if block.strip()]

    paragraphs: list[Paragraph] = []
    current_part: str | None = None
    current_item: str | None = None

    for block in blocks:
        for segment in split_long_text(block, max_tokens=max_tokens):
            heading, heading_path = detect_section_heading(segment)
            if heading:
                if heading.upper().startswith("PART "):
                    current_part = heading
                    current_item = None
                elif heading.upper().startswith("ITEM "):
                    current_item = heading

            section_path = " > ".join(part for part in (current_part, current_item) if part) or None
            section = current_item or current_part
            paragraphs.append(
                Paragraph(
                    text=segment,
                    section=section,
                    section_path=section_path,
                    token_count=estimate_token_count(segment),
                )
            )

    return paragraphs


def render_chunk_text(paragraphs: list[Paragraph], section_path: str | None) -> str:
    body = "\n\n".join(paragraph.text for paragraph in paragraphs).strip()
    if not section_path:
        return body

    first_text = paragraphs[0].text.lstrip()
    if first_text.upper().startswith(section_path.upper()):
        return body
    return f"{section_path}\n\n{body}"


def chunk_filing(filing: FilingRecord, settings: Settings) -> list[ChunkRecord]:
    paragraphs = extract_paragraphs(
        filing.raw_text,
        max_tokens=max(settings.chunk_size_tokens, settings.chunk_overlap_tokens, 1),
    )
    if not paragraphs:
        return []

    chunks: list[ChunkRecord] = []
    current: list[Paragraph] = []
    current_tokens = 0
    chunk_index = 0

    def flush_chunk(buffer: list[Paragraph], index: int) -> ChunkRecord:
        section_path = next((paragraph.section_path for paragraph in buffer if paragraph.section_path), None)
        section = next((paragraph.section for paragraph in buffer if paragraph.section), None)
        text = render_chunk_text(buffer, section_path)
        return build_chunk_record(
            filing,
            chunk_index=index,
            text=text,
            section=section,
            section_path=section_path,
        )

    for paragraph in paragraphs:
        exceeds_target = current and current_tokens + paragraph.token_count > settings.chunk_size_tokens
        if exceeds_target:
            chunks.append(flush_chunk(current, chunk_index))
            chunk_index += 1

            overlap: list[Paragraph] = []
            overlap_tokens = 0
            for prior in reversed(current):
                overlap.insert(0, prior)
                overlap_tokens += prior.token_count
                if overlap_tokens >= settings.chunk_overlap_tokens:
                    break

            current = overlap
            current_tokens = sum(item.token_count for item in current)

        current.append(paragraph)
        current_tokens += paragraph.token_count

    if current:
        chunks.append(flush_chunk(current, chunk_index))

    return chunks


def materialize_chunk_records(filings: list[FilingRecord], settings: Settings) -> list[ChunkRecord]:
    chunk_records: list[ChunkRecord] = []
    for filing in filings:
        chunk_records.extend(chunk_filing(filing, settings))
    return chunk_records


def write_chunk_artifact(settings: Settings, chunks: list[ChunkRecord]) -> Path:
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    output_path = settings.chunk_artifact_path
    with output_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.to_dict(), ensure_ascii=True))
            handle.write("\n")
    return output_path
