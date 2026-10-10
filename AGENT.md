# AGENT.md — Panduan AI Coding Assistant (v2)

Baca berurutan: `PRD.md` (v2), file ini, lalu `data/roles/roles.json`. Jika ada bentrok dengan instruksi lama atau riwayat percakapan sebelumnya, `PRD.md` v2 dan file ini yang berlaku.

## Protokol Kerja (wajib)

1. **Satu tahap per sesi.** Kerjakan hanya scope yang diminta. Jangan menyentuh file di luar scope.
2. **Jalankan, jangan menebak.** Laporkan keluaran dan angka nyata. Jika sesuatu tidak bisa diuji (misalnya dialog pemilih file di browser), tulis eksplisit "belum teruji". Jangan mengklaim berhasil.
3. **Setelah selesai, laporkan lalu berhenti** dan tunggu konfirmasi pemilik proyek (Chris). Jangan lanjut ke tahap berikutnya sendiri.
4. **Perubahan yang mempengaruhi skor atau ranking:** jalankan evaluasi sebelum dan sesudah, laporkan tabel perbandingan, dan jangan mengganti mode default tanpa persetujuan.
5. **Pemeriksaan regresi:** mode `full` harus tetap menghasilkan skor berikut untuk 6 CV valid dengan JD uji di bawah (urutan: DATA01, DATA03, DATA04, DATA02, DATA06, DATA05):
   `0,3597 / 0,2768 / 0,2728 / 0,2484 / 0,2108 / 0,0398`
   JD uji regresi: `Backend Developer: membangun dan memelihara aplikasi backend serta REST API menggunakan Python, database SQL, pengujian perangkat lunak, dan kolaborasi tim. Pengalaman pengembangan software dan pemecahan masalah sistem menjadi nilai tambah.`
6. **Jangan menghapus atau menimpa fungsi lama yang sudah tervalidasi** (`rank_resumes` mode `full`, `explain.get_matched_keywords`). Tambahkan kode baru di sampingnya.

## Keputusan Teknis yang Final

- Bahasa: Python. PEP8 dasar, nama fungsi dan variabel dalam bahasa Inggris, komentar boleh bahasa Indonesia.
- Stack: PyMuPDF (`import pymupdf as fitz`), python-docx, sentence-transformers, scikit-learn, pandas, FastAPI, Streamlit.
- **Dilarang:** spaCy untuk teks Indonesia, OCR, language detection eksplisit, fine-tuning atau pelatihan model.
- Role hanya `frontend` dan `backend`.
- Jangan menampilkan skor sebagai persentase kecocokan. Label UI: "Skor kemiripan (relatif)".
- Penjelasan di UI harus diberi keterangan bahwa itu heuristik, bukan uraian perhitungan embedding.

## Fakta Model

- Model: `paraphrase-multilingual-MiniLM-L12-v2`, dimuat sekali di level module.
- `max_seq_length = 128`. Teks lebih panjang dipotong diam-diam, termasuk template JD.
- Saat template dimuat, hitung jumlah token dengan tokenizer model dan beri peringatan jika lebih dari 128.
- Chunk: maksimal 80 kata, tanpa overlap, lalu dipangkas agar tidak melebihi 128 token. Gunakan encode batch.

## Struktur Proyek (v2)

```
resume-ranker/
├── app/
│   ├── main.py            # FastAPI: /health, /roles, /rank
│   ├── extract.py         # PDF/DOCX -> teks
│   ├── preprocess.py      # cleaning + SECTION_MAP
│   ├── embed.py           # model sekali load
│   ├── chunk.py           # chunking token-safe
│   ├── rank.py            # mode skor: full | chunk_max | chunk_top3
│   ├── roles.py           # memuat roles.json
│   ├── lexicon.py         # deteksi skill (found/missing)
│   └── explain.py         # fungsi lama, dipertahankan
├── streamlit_app.py
├── data/
│   ├── roles/roles.json   # template role + lexicon (DRAFT, perlu review)
│   ├── labels/labels.csv  # label manual (tanpa nama orang)
│   ├── sample_cvs/        # CV sampel (jangan di-commit)
│   └── kaggle_subset/     # subset kecil saja
├── evaluation/
│   ├── run_eval.py        # evaluasi deterministik
│   ├── baselines.py       # TF-IDF, lexicon, acak
│   └── results/           # keluaran CSV
├── scripts/diag_truncation.py
├── requirements.txt
├── .gitignore
├── PRD.md
├── AGENT.md
└── README.md
```

## Kontrak API v2

- `GET /health` -> `{"status": "ok"}`
- `GET /roles` -> `{"roles": [{"id", "label", "template_id", "template_en"}]}`, sumbernya `roles.json`.
- `POST /rank` (multipart): `role` (`frontend` | `backend`, wajib), `jd_text` (wajib), `files` (minimal satu).
  - Setiap file disimpan sementara (`tempfile`), diproses, lalu dihapus di `finally`.
  - Kegagalan per file ditangkap dan dicatat di `excluded`. Satu file gagal tidak menghentikan request.
  - Teks kosong setelah preprocessing masuk `excluded`, bukan diberi skor.
  - 400 untuk `jd_text` kosong, tanpa file, atau `role` tidak dikenal.
  - Response: `role`, `ranking` (`filename`, `score`, `skills_found`, `skills_missing`, `evidence`), dan `excluded` (`filename`, `reason`). Contoh lengkap ada di `PRD.md` bagian 7.
- Streamlit hanya memanggil API lewat HTTP. Jangan memanggil fungsi pipeline langsung dari UI.

## Lexicon dan `roles.json`

- Cocokkan alias pada teks yang **hanya di-lowercase dan spasinya dirapatkan**. Jangan pakai `clean_text()`, karena simbol `+`, `#`, dan `.` penting untuk `c#`, `.net`, `node.js`.
- Pola regex per alias: `(?<![a-z0-9+#.])ALIAS_ESCAPED(?![a-z0-9+#])` dengan `re.escape`.
- Kasus uji wajib: `java` tidak cocok di dalam `javascript`; `sql` tidak cocok di dalam `mysql` atau `nosql`; `github` cocok dengan skill `git`; `node.js` dan `.net` terdeteksi.
- Periksa juga apa yang dilakukan `preprocess()` terhadap `C++ C# .NET Node.js` dan laporkan hasilnya.
- Hitung "skill belum ditemukan" dari `core_skills` dan `core_groups` role terpilih. Grup memakai logika `any_of`.
- `roles.json` berstatus DRAFT. Jangan mengubah isinya tanpa persetujuan pemilik proyek.

## Data dan Privasi

- Dataset besar disimpan di luar repo. Path dibaca dari environment variable `RESUME_DATASET_DIR`. Jangan memuat atau meng-embed seluruh dataset.
- Sampling harus deterministik (seed tetap) dan dicatat di keluaran.
- `.gitignore` wajib mencakup `data/sample_cvs/`, `data/kaggle_subset/`, dataset besar, dan `evaluation/results/` bila berisi data mentah.
- Jangan mencetak isi CV ke log atau keluaran diagnosis. Cukup angka dan metadata teknis.
- `labels.csv` hanya memuat `cv_id`, bukan nama orang. Jangan mengubah label, dan jangan memilih subset berdasarkan skor sistem.

## Evaluasi

- Skrip deterministik. Cetak konfigurasi di keluaran: mode skor, K, ukuran chunk, versi model, jumlah CV per label.
- Metrik dan baseline mengikuti `PRD.md` bagian 11. Simpan hasil ke `evaluation/results/*.csv`.
- Laporkan jumlah data tiap kelas di samping setiap metrik. Jangan menyajikan angka dari sampel kecil sebagai estimasi umum.

## Menjalankan (Windows)

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload       # backend
python -m streamlit run streamlit_app.py      # frontend (terminal terpisah)
```

Gunakan `python -m` agar interpreter yang dipakai adalah yang memiliki dependensi proyek.

## Batasan yang Harus Terlihat di UI atau Dokumentasi

- Ekstraksi teks bisa gagal pada PDF hasil scan atau layout kompleks.
- Skor menunjukkan kemiripan semantik relatif, bukan kemampuan kandidat.
- Deteksi skill berbasis lexicon dan tidak mencakup semua istilah.
- Hasil evaluasi berasal dari sampel kecil dan belum tentu berlaku umum.
- Sistem adalah alat bantu keputusan, bukan penyaring otomatis.