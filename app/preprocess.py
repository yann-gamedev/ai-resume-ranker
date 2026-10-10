"""Normalize resume section headers and clean extracted text."""

import re
from pathlib import Path

SECTION_MAP = {
    "pengalaman kerja": "experience",
    "work experience": "experience",
    "riwayat pendidikan": "education",
    "education": "education",
    "keahlian": "skills",
    "skills": "skills",
    "jenjang pendidikan": "education",
    "pengalaman organisasi": "experience",
    "keterampilan": "skills",
}

_HEADER_PATTERN = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(key) for key in SECTION_MAP) + r")(?!\w)",
    flags=re.IGNORECASE,
)


def normalize_headers(text: str) -> str:
    """Replace known Indonesian and English section names without changing other text."""
    return _HEADER_PATTERN.sub(lambda match: SECTION_MAP[match.group().lower()], text)


def clean_text(text: str) -> str:
    """Lowercase and collapse whitespace while retaining letters and numbers."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def preprocess(text: str) -> str:
    """Normalize known section names, then clean the remaining text."""
    return clean_text(normalize_headers(text))


if __name__ == "__main__":
    import sys

    # Permit both `python app/preprocess.py` and `python -m app.preprocess`.
    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.extract import extract_text

    project_dir = Path(__file__).resolve().parent.parent
    sample_dir = project_dir / "data" / "sample_cvs"
    samples = sorted(
        file for file in sample_dir.iterdir()
        if file.is_file() and file.suffix.lower() in {".pdf", ".docx"}
    ) if sample_dir.exists() else []
    if not samples:
        print(f"No PDF/DOCX files found in {sample_dir}; preprocessing test skipped.")

    debug_dir = project_dir / "data" / "sample_cvs_debug"
    debug_written = False
    for sample in samples:
        try:
            raw = extract_text(str(sample))
            cleaned = preprocess(raw)
        except ValueError as exc:
            print(f"{sample.name}: failed to extract: {exc}")
            continue

        found = {
            header: bool(re.search(rf"\b{header}\b", cleaned))
            for header in ("experience", "education", "skills")
        }
        print(
            f"{sample.name}: before={len(raw)} chars, after={len(cleaned)} chars; "
            + ", ".join(f"{header}={'yes' if present else 'no'}" for header, present in found.items())
        )
        if not debug_written:
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_path = debug_dir / f"{sample.stem}_clean.txt"
            debug_path.write_text(cleaned, encoding="utf-8")
            print(f"Full cleaned text saved to {debug_path}")
            debug_written = True

