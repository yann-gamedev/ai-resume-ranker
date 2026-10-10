"""Evaluate Precision@K for IT and engineering JDs against a mixed CSV subset."""

import sys
import time
from pathlib import Path

import pandas as pd

K = 5
POSITIVE_COUNT = 20
NEGATIVE_COUNT = 10
TARGET_CATEGORY = "INFORMATION-TECHNOLOGY"
SECOND_CATEGORY = "ENGINEERING"
CONTROL_CATEGORY = "HR"


def main() -> None:
    """Print category counts first, then rank a reproducible mixed subset."""
    started = time.time()
    csv_path = Path(__file__).resolve().parent.parent / "data" / "kaggle_subset" / "Resume.csv"
    data = pd.read_csv(csv_path)

    # Show exact labels before selecting a target or loading the ranking model.
    print("Kategori (nilai persis) dan jumlah baris:", flush=True)
    for category, count in data["Category"].value_counts(dropna=False).items():
        print(f"{category!r}: {count}", flush=True)

    for category in (TARGET_CATEGORY, SECOND_CATEGORY, CONTROL_CATEGORY):
        if category not in data["Category"].values:
            raise ValueError(f"Target/control category {category!r} tidak ditemukan di CSV")
    if "Resume_str" not in data.columns:
        raise ValueError("Kolom Resume_str tidak ditemukan di CSV")

    # Stable but order-biased: first matching CSV rows per category, no random seed.
    positives = data.loc[data["Category"] == TARGET_CATEGORY].head(POSITIVE_COUNT)
    engineering = data.loc[data["Category"] == SECOND_CATEGORY].head(NEGATIVE_COUNT)
    controls = data.loc[data["Category"] == CONTROL_CATEGORY].head(NEGATIVE_COUNT)
    negatives = pd.concat([engineering, controls])
    subset = pd.concat([positives, negatives]).sort_index()
    if len(subset) < K:
        raise ValueError(f"Subset hanya memiliki {len(subset)} baris, kurang dari K={K}")
    print(
        f"\nSubset deterministik: {len(positives)} IT + {len(negatives)} non-IT "
        f"= {len(subset)} resume; key adalah index baris CSV asli."
    )
    print("Komposisi non-IT:")
    for category, count in negatives["Category"].value_counts().items():
        print(f"  {category!r}: {count}")
    print(
        "Metode: ambil 20 baris pertama INFORMATION-TECHNOLOGY, 10 baris pertama "
        "ENGINEERING, dan 10 baris pertama HR menurut urutan CSV; gabungkan, urutkan "
        "berdasarkan indeks CSV asli. Tanpa acak/seed; pemilihan awal per kategori "
        "berisiko selection bias dan tidak mewakili keseluruhan dataset."
    )

    # Allow running as `python evaluation/precision_at_k.py` from the project root.
    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.rank import rank_resumes

    test_cases = [
        {
            "jd_text": (
                "Backend Developer: membangun dan memelihara aplikasi backend serta REST API "
                "menggunakan Python, database SQL, pengujian perangkat lunak, dan kolaborasi tim. "
                "Pengalaman pengembangan software dan pemecahan masalah sistem menjadi nilai tambah."
            ),
            "target_category": TARGET_CATEGORY,
        },
        {
            "jd_text": (
                "Engineering: merancang dan mengembangkan sistem teknis, menganalisis "
                "kebutuhan, melakukan pengujian, pemecahan masalah, serta bekerja "
                "dengan tim lintas disiplin untuk meningkatkan kualitas produk."
            ),
            "target_category": SECOND_CATEGORY,
        },
    ]
    scores = []
    cv_texts = {int(index): str(row["Resume_str"]) if pd.notna(row["Resume_str"]) else ""
                for index, row in subset.iterrows()}
    for case in test_cases:
        ranking, skipped_files = rank_resumes(case["jd_text"], cv_texts)
        top_k = ranking[:K]
        matches = sum(subset.loc[index, "Category"] == case["target_category"] for index, _ in top_k)
        precision = matches / K
        scores.append(precision)
        print(f"\nJD: {case['jd_text'][:50]}")
        print(f"Target category: {case['target_category']}; K={K}")
        print(f"{'CSV row':<10} {'Score':>10}  Actual category")
        print("-" * 48)
        for index, score in top_k:
            print(f"{index:<10} {score:>10.4f}  {subset.loc[index, 'Category']}")
        print(f"Precision@{K}: {precision:.4f} ({matches}/{K})")
        if skipped_files:
            print(f"File/baris dilewati: {len(skipped_files)}")
    print(f"\nRata-rata Precision@{K}: {sum(scores) / len(scores):.4f}")
    print(f"Waktu eksekusi total: {time.time() - started:.2f} detik")


if __name__ == "__main__":
    main()

