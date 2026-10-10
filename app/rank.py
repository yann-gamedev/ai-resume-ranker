"""Rank raw resume texts against one job description."""

import time
from pathlib import Path

# Start timing before importing the embedding module so the CLI includes model load.
_start_time = time.time() if __name__ == "__main__" else None

from sklearn.metrics.pairwise import cosine_similarity

from app.embed import get_embedding
from app.preprocess import preprocess


def rank_resumes(
    jd_text: str, cv_texts: dict[str, str]
) -> tuple[list[tuple[str, float]], list[tuple[str, str]]]:
    """Return ranked resumes and files skipped because their extracted text is empty."""
    if not cv_texts:
        return [], []

    jd_embedding = get_embedding(preprocess(jd_text))
    results = []
    skipped_files = []
    for filename, raw_text in cv_texts.items():
        cleaned_text = preprocess(raw_text)
        if not cleaned_text.strip():
            skipped_files.append(
                (filename, "teks kosong setelah ekstraksi - kemungkinan PDF hasil scan")
            )
            continue
        cv_embedding = get_embedding(cleaned_text)
        score = float(cosine_similarity([jd_embedding], [cv_embedding])[0, 0])
        results.append((filename, score))
    return sorted(results, key=lambda item: item[1], reverse=True), skipped_files


if __name__ == "__main__":
    from app.extract import extract_text

    sample_dir = Path(__file__).resolve().parent.parent / "data" / "sample_cvs"
    files = sorted(
        path for path in sample_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".pdf", ".docx"}
    ) if sample_dir.exists() else []
    jd = (
        "Backend Developer: membangun dan memelihara aplikasi backend serta REST API "
        "menggunakan Python, database SQL, pengujian perangkat lunak, dan kolaborasi tim. "
        "Pengalaman pengembangan software dan pemecahan masalah sistem menjadi nilai tambah."
    )
    cvs = {}
    for path in files:
        try:
            cvs[path.name] = extract_text(str(path))
        except ValueError as exc:
            print(f"Failed to extract {path.name}: {exc}")

    if not cvs:
        print("No readable PDF/DOCX sample CVs found; ranking skipped.")
        ranked, skipped_files = [], []
    else:
        ranked, skipped_files = rank_resumes(jd, cvs)
        print("Ranking:")
        print(f"{'File':<36} {'Score':>8}")
        print("-" * 45)
        for filename, score in ranked:
            print(f"{filename:<36} {score:>8.4f}")

    print("File dilewati:")
    if skipped_files:
        for filename, reason in skipped_files:
            print(f"- {filename}: {reason}")
    else:
        print("- Tidak ada")
    print(f"Total execution time: {time.time() - _start_time:.2f} seconds")

