"""Extract raw text from PDF and DOCX documents without preprocessing."""

from pathlib import Path
from zipfile import BadZipFile

import pymupdf as fitz
from docx import Document


def extract_text_from_pdf(path: str) -> str:
    """Return raw text from every PDF page, separated by newlines."""
    try:
        with fitz.open(path) as document:
            return "\n".join(page.get_text() for page in document)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError(f"Failed to open or read PDF '{path}' (file may be corrupt): {exc}") from exc


def extract_text_from_docx(path: str) -> str:
    """Return raw text from every DOCX paragraph, separated by newlines."""
    try:
        document = Document(path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    except (OSError, ValueError, KeyError, RuntimeError, BadZipFile) as exc:
        raise ValueError(f"Failed to open or read DOCX '{path}' (file may be corrupt): {exc}") from exc


def extract_text(path: str) -> str:
    """Extract raw text from a PDF or DOCX, rejecting other formats."""
    extension = Path(path).suffix.lower()
    if extension == ".pdf":
        return extract_text_from_pdf(path)
    if extension == ".docx":
        return extract_text_from_docx(path)
    raise ValueError(f"Unsupported file extension '{extension or '(none)'}' for '{path}'. Supported extensions: .pdf, .docx")


if __name__ == "__main__":
    sample_dir = Path(__file__).resolve().parent.parent / "data" / "sample_cvs"
    samples = sorted(
        file for file in sample_dir.iterdir()
        if file.is_file() and file.suffix.lower() in {".pdf", ".docx"}
    )[:2]
    if not samples:
        print(f"No PDF/DOCX samples found in {sample_dir}. Add real CV files there and rerun this module; extraction test skipped.")
    for sample in samples:
        try:
            text = extract_text(str(sample))
            print(f"{sample.name}: {len(text)} characters\nPreview (first 300 characters):\n{text[:300]}\n")
        except ValueError as exc:
            print(f"{sample.name}: {exc}")
