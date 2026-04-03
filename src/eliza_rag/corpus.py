from __future__ import annotations

import json
import re
import zipfile
from collections import Counter
from pathlib import Path

from .config import Settings
from .models import ChunkRecord, CorpusInspection, FilingRecord

FILENAME_RE = re.compile(
    r"^(?P<ticker>[A-Z]+)_(?P<form_type>10K|10Q)_(?:(?P<fiscal_period>\d{4}Q[1-4])_)?"
    r"(?P<filing_date>\d{4}-\d{2}-\d{2})_full\.txt$"
)


def ensure_corpus_directory(settings: Settings) -> Path:
    if settings.corpus_dir.exists():
        return settings.corpus_dir

    if not settings.corpus_zip_path.exists():
        raise FileNotFoundError(
            f"Corpus directory {settings.corpus_dir} and archive {settings.corpus_zip_path} are both missing."
        )

    settings.data_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(settings.corpus_zip_path) as archive:
        archive.extractall(settings.data_dir)

    extracted_dir = settings.data_dir / "edgar_corpus"
    if extracted_dir.exists():
        return extracted_dir

    raise FileNotFoundError(
        f"Expected extracted corpus directory at {extracted_dir}, but it was not created by the archive."
    )


def load_manifest(manifest_path: Path) -> dict[str, object] | None:
    if not manifest_path.exists():
        return None

    with manifest_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_filing_paths(corpus_dir: Path) -> list[Path]:
    return sorted(path for path in corpus_dir.glob("*.txt") if path.is_file())


def parse_filename_metadata(file_name: str) -> dict[str, str | None]:
    match = FILENAME_RE.match(file_name)
    if not match:
        raise ValueError(f"Unsupported filing filename format: {file_name}")
    metadata = match.groupdict()
    metadata["form_type"] = metadata["form_type"].replace("10K", "10-K").replace("10Q", "10-Q")
    return metadata


def parse_header_metadata(raw_text: str) -> dict[str, str]:
    header: dict[str, str] = {}

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if set(stripped) == {"="}:
            break
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        header[key.strip()] = value.strip()

    return header


def build_filing_record(path: Path, manifest_files: set[str] | None = None) -> FilingRecord:
    metadata = parse_filename_metadata(path.name)
    raw_text = path.read_text(encoding="utf-8")
    header = parse_header_metadata(raw_text)

    return FilingRecord(
        filing_id=path.stem,
        ticker=metadata["ticker"] or "",
        form_type=metadata["form_type"] or "",
        filing_date=metadata["filing_date"] or "",
        fiscal_period=header.get("Quarter") or metadata["fiscal_period"],
        source_path=str(path),
        raw_text=raw_text,
        company_name=header.get("Company"),
        report_period=header.get("Report Period"),
        cik=header.get("CIK"),
        manifest_listed=(path.name in manifest_files) if manifest_files is not None else None,
    )


def build_chunk_record(
    filing: FilingRecord,
    *,
    chunk_index: int,
    text: str,
    section: str | None = None,
    section_path: str | None = None,
) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=f"{filing.filing_id}::chunk-{chunk_index:04d}",
        filing_id=filing.filing_id,
        ticker=filing.ticker,
        form_type=filing.form_type,
        filing_date=filing.filing_date,
        fiscal_period=filing.fiscal_period,
        source_path=filing.source_path,
        chunk_index=chunk_index,
        text=text,
        company_name=filing.company_name,
        section=section,
        section_path=section_path,
    )


def inspect_corpus(settings: Settings) -> tuple[CorpusInspection, list[FilingRecord]]:
    corpus_dir = ensure_corpus_directory(settings)
    manifest = load_manifest(corpus_dir / "manifest.json")
    manifest_files = set(manifest.get("files", [])) if manifest else None

    filing_paths = iter_filing_paths(corpus_dir)
    filings: list[FilingRecord] = []
    parse_failures: list[str] = []

    for path in filing_paths:
        try:
            filings.append(build_filing_record(path, manifest_files))
        except ValueError:
            parse_failures.append(path.name)

    filing_types = Counter(filing.form_type for filing in filings)
    tickers = sorted({filing.ticker for filing in filings})
    filing_dates = sorted(filing.filing_date for filing in filings)

    discovered_files = {path.name for path in filing_paths}
    manifest_file_names = manifest_files or set()

    inspection = CorpusInspection(
        corpus_dir=str(corpus_dir),
        manifest_path=str(corpus_dir / "manifest.json") if manifest else None,
        manifest_present=manifest is not None,
        manifest_file_count=int(manifest["file_count"]) if manifest and "file_count" in manifest else None,
        discovered_file_count=len(filing_paths),
        tickers=tickers,
        filing_types=dict(sorted(filing_types.items())),
        filing_date_range={
            "min": filing_dates[0] if filing_dates else None,
            "max": filing_dates[-1] if filing_dates else None,
        },
        manifest_missing_files=sorted(manifest_file_names - discovered_files),
        unlisted_files=sorted(discovered_files - manifest_file_names) if manifest else [],
        filename_parse_failures=sorted(parse_failures),
        sample_filing_ids=[filing.filing_id for filing in filings[:5]],
    )

    return inspection, filings


def write_inspection_artifact(settings: Settings, inspection: CorpusInspection) -> Path:
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    output_path = settings.artifacts_dir / "corpus_inspection.json"
    output_path.write_text(json.dumps(inspection.to_dict(), indent=2), encoding="utf-8")
    return output_path
