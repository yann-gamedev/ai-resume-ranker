"""Explain rankings through simple bilingual keyword overlap."""

from pathlib import Path

STOPWORDS = {
    "ada", "agar", "akan", "adalah", "atau", "bagi", "dalam", "dan", "dari",
    "dengan", "di", "ini", "itu", "juga", "ke", "kepada", "lebih", "melalui",
    "oleh", "pada", "para", "sebagai", "serta", "sudah", "telah", "tentang",
    "terhadap", "untuk", "yang", "yaitu", "a", "an", "and", "are", "as",
    "at", "be", "by", "for", "from", "has", "have", "in", "into", "is",
    "it", "of", "on", "or", "our", "that", "the", "their", "this", "to",
    "was", "were", "will", "with", "you", "your",
    "menggunakan", "menjadi", "pengalaman", "tim", "sistem", "nilai", "tambah",
    "dapat", "experience", "team", "using", "work", "ability", "skills", "knowledge",
}


def get_matched_keywords(
    jd_text_clean: str, cv_text_clean: str, top_n: int = 10
) -> list[str]:
    """Return up to top_n alphabetically sorted shared informative words."""
    jd_words = {word for word in jd_text_clean.split() if len(word) >= 3 and word not in STOPWORDS}
    cv_words = {word for word in cv_text_clean.split() if len(word) >= 3 and word not in STOPWORDS}
    return sorted(jd_words & cv_words)[:top_n]


if __name__ == "__main__":
    import sys

    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.extract import extract_text
    from app.preprocess import preprocess

    sample_dir = Path(__file__).resolve().parent.parent / "data" / "sample_cvs"
    jd_text = (
        "Backend Developer: membangun dan memelihara aplikasi backend serta REST API "
        "menggunakan Python, database SQL, pengujian perangkat lunak, dan kolaborasi tim. "
        "Pengalaman pengembangan software dan pemecahan masalah sistem menjadi nilai tambah."
    )
    jd_clean = preprocess(jd_text)
    for filename in ("DATA01.pdf", "DATA02.pdf"):
        sample = sample_dir / filename
        matched = get_matched_keywords(jd_clean, preprocess(extract_text(str(sample))))
        print(f"Keyword cocok untuk {filename}: {matched}")

