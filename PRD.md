# Product Requirements Document (PRD) — v2
## AI-Based Resume Ranker: Ranking CV Berbasis Role (Frontend / Backend)

**Status:** v2, menggantikan v1. Konteks: Inception Hackathon.
**Arah baru:** pengguna memilih role target lewat dropdown, JD template terisi otomatis dan masih bisa diedit, semua CV diurutkan untuk role itu, dan hasilnya disertai penjelasan yang mudah dipahami.

---

## 0. Perubahan dari v1

| Aspek | v1 | v2 | Alasan |
|---|---|---|---|
| Input JD | Teks bebas | Dropdown role (Frontend/Backend), template JD terisi otomatis dan bisa diedit | JD konsisten dan cukup deskriptif, tidak bergantung pada kemampuan pengguna menulis JD |
| Skor | Satu embedding untuk seluruh teks CV | Skema dipilih lewat ablasi: `full`, `chunk_max`, `chunk_top3` | Diagnosis: model hanya membaca 128 token pertama (9,92%–42,38% isi CV yang diuji) dan peringkat berubah saat seluruh teks dibaca |
| Penjelasan | Overlap kata literal | Skill terdeteksi (lexicon), skill inti yang belum ditemukan, kutipan bagian CV terbaik | Overlap literal didominasi kata generik seperti "pengalaman" dan "tim" |
| Evaluasi | Proxy kategori Kaggle | Set berlabel manual + baseline + ablasi; proxy Kaggle jadi pelengkap | Proxy kategori tidak mengukur Frontend vs Backend dan bisa terpengaruh judul jabatan di awal resume |
| Data | ±15 CV + subset CSV | + dataset Kaggle versi lengkap + CV kontribusi tim | Butuh ground truth yang cukup |

## 1. Ringkasan Produk

Rekruter memilih role target (Frontend atau Backend), meninjau atau mengedit JD template, mengunggah CV (PDF/DOCX), lalu sistem mengurutkan CV berdasarkan kemiripan semantik dengan JD. Setiap kandidat disertai: skill yang terdeteksi, skill inti role yang belum ditemukan, dan kutipan bagian CV yang paling relevan.

## 2. Problem Statement

Penyaringan CV manual lambat, dan pencocokan kata kunci klasik gagal menangkap kemiripan makna serta mudah dikelabui keyword stuffing. Untuk pelamar Indonesia, CV sering bercampur bahasa Indonesia dan Inggris. Ranking tanpa penjelasan juga sulit dipercaya pengguna, jadi sistem harus menunjukkan alasan yang bisa diperiksa.

## 3. Tujuan

- T1: MVP end-to-end: pilih role, unggah CV, lihat ranking dan alasan.
- T2: Skor yang mempertimbangkan seluruh isi CV, bukan hanya 128 token pertama.
- T3: Penjelasan yang dipahami pengguna non-teknis.
- T4: Evaluasi terukur terhadap label manual dan baseline, dengan limitasi dilaporkan jujur.
- T5: Mendukung CV dan template berbahasa Indonesia dan Inggris.

## 4. Scope

**Dalam scope**
- Dua role: Frontend Developer dan Backend Developer.
- Template JD per role dalam bahasa Indonesia dan Inggris, bisa diedit pengguna.
- Ranking semua CV unggahan untuk satu role per proses.
- Penjelasan: skill terdeteksi, skill inti yang belum ada, kutipan bukti.
- Evaluasi terhadap set berlabel manual.

**Di luar scope**
- OCR untuk CV hasil scan (file seperti ini dilewati dan dilaporkan).
- Role selain Frontend dan Backend.
- Login/autentikasi, penyimpanan CV permanen.
- Fine-tuning atau pelatihan model.
- Keputusan otomatis (auto-reject). Sistem hanya alat bantu keputusan.

## 5. Alur Pengguna

1. Pilih role di dropdown (Frontend atau Backend).
2. Pilih bahasa template (Indonesia atau Inggris). Kotak JD terisi otomatis.
3. Edit JD bila perlu.
4. Unggah satu atau lebih CV (PDF/DOCX).
5. Klik "Ranking CV".
6. Lihat tabel ranking. Detail kandidat peringkat 1 terbuka secara default, dan pengguna bisa memilih kandidat lain untuk melihat detailnya.
7. File yang dilewati ditampilkan terpisah beserta alasannya.

## 6. Fitur

### MVP
1. Dropdown role dan prefill JD dari template (`GET /roles` sebagai sumber tunggal template).
2. Ranking dengan skema skor terpilih (lihat bagian 8).
3. Penjelasan: skill terdeteksi, skill inti yang belum ditemukan, kutipan bukti.
4. Penanganan file bermasalah: dilewati dengan alasan eksplisit, tidak menghentikan proses.
5. Skrip evaluasi yang bisa dijalankan ulang (deterministik).

### Stretch
1. Skor kemiripan CV terhadap kedua role sekaligus (kolom Frontend dan Backend), untuk menandai CV fullstack.
2. Export hasil ranking ke CSV.
3. Menyorot istilah skill di dalam kutipan bukti.
4. Eksperimen prototipe bilingual (rata-rata embedding template ID dan EN).

## 7. Arsitektur dan Kontrak API

```
roles.json --> GET /roles --> Streamlit (dropdown, prefill JD)
                                   | POST /rank (role, jd_text, files)
                                   v
 upload -> temp file -> extract -> preprocess -> chunk -> embed (batch) -> skor -> ranking
                                   |
                                   +--> lexicon (skill ditemukan/hilang) + chunk terbaik (bukti)
```

**Endpoint**
- `GET /health` -> `{"status": "ok"}`
- `GET /roles` -> daftar role dengan `id`, `label`, dan template `id`/`en`.
- `POST /rank` (multipart): `role` (`frontend` | `backend`, wajib), `jd_text` (wajib), `files` (minimal satu).

**Response `/rank`**
```json
{
  "role": "backend",
  "ranking": [
    {
      "filename": "CV01.pdf",
      "score": 0.51,
      "skills_found": ["sql", "docker"],
      "skills_missing": ["Autentikasi", "Bahasa backend (Python/Java/Node.js/...)"],
      "evidence": {"text": "...", "score": 0.51}
    }
  ],
  "excluded": [{"filename": "CV07.pdf", "reason": "teks kosong setelah ekstraksi - kemungkinan PDF hasil scan"}]
}
```
Error 400 untuk: `jd_text` kosong, tidak ada file, atau `role` tidak dikenal.

## 8. Skema Skor

Temuan diagnosis: `paraphrase-multilingual-MiniLM-L12-v2` memiliki `max_seq_length = 128`. Teks lebih panjang dipotong tanpa peringatan, sehingga CV yang diuji hanya terbaca 9,92%–42,38%. Template JD juga terkena batas ini.

| Mode | Cara | Catatan |
|---|---|---|
| `full` | Embedding teks penuh (terpotong 128 token) | Baseline v1, dipertahankan untuk pemeriksaan regresi |
| `chunk_max` | Skor = cosine tertinggi antar chunk | Menangkap bagian paling relevan, rentan terhadap satu chunk yang kebetulan mirip |
| `chunk_top3` | Rata-rata 3 chunk teratas (atau semua chunk bila kurang dari 3) | Lebih stabil, tapi bisa mengencerkan CV yang hanya punya satu bagian relevan |

**Spesifikasi chunking:** maksimal 80 kata per chunk, tanpa overlap, dan dipangkas lebih lanjut agar tidak melebihi 128 token menurut tokenizer model. Encode dilakukan secara batch.

Skala skor berbeda antar mode (`chunk_max` cenderung lebih tinggi), jadi skor tidak dibandingkan lintas mode. Skor adalah kemiripan relatif dalam satu JD, bukan persentase kecocokan.

**Mode default belum diputuskan.** Pilihan ditentukan oleh evaluasi di set berlabel (bagian 11).

## 9. Penjelasan (Explainability)

Tiga komponen per kandidat:
1. **Skill terdeteksi:** skill dari lexicon (`data/roles/roles.json`) yang ditemukan di CV dan relevan untuk role terpilih.
2. **Skill inti yang belum ditemukan:** dari daftar inti role. Bahasa pemrograman dan framework dikelompokkan (`any_of`) supaya kandidat Python tidak dianggap kurang karena tidak memakai Java.
3. **Kutipan bukti:** teks chunk dengan skor tertinggi (ditampilkan ±40–80 kata).

Aturan tampilan:
- Beri keterangan bahwa penjelasan ini heuristik dan bukan uraian perhitungan embedding.
- Skor diberi label "Skor kemiripan (relatif)".
- Kutipan bisa memuat data pribadi. Tampilkan hanya di UI, jangan dicetak ke log.

## 10. Data dan Protokol Pelabelan

**Sumber data**
- CV sampel tim (`DATA01`–`DATA07` dan tambahan berikutnya, bilingual ID/EN).
- Dataset Kaggle versi lengkap (±2 GB, struktur folder dan kategori dikonfirmasi setelah unduhan selesai).
- CV kontribusi tim atau teman (dengan izin dan dianonimkan).

**Label** (satu label per CV)

| Label | Definisi |
|---|---|
| Frontend | Pengalaman nyata (proyek/pekerjaan) terutama di antarmuka web atau sisi klien |
| Backend | Pengalaman nyata terutama di logika server, API, database, atau layanan |
| Fullstack | Pengalaman nyata di keduanya, bukan sekadar daftar skill |
| Lainnya | Tidak ada bukti pengalaman pengembangan Frontend/Backend (IT support, manajer, jaringan, non-IT, mobile atau data murni) |

**Aturan**
- Label hanya berdasarkan isi CV. Pelabel tidak boleh melihat skor sistem.
- Minimal 2 pelabel untuk sedikitnya 20 CV; hitung agreement (Cohen's kappa). Perbedaan diselesaikan lewat diskusi dan label final dicatat.
- Lexicon boleh dipakai untuk menyaring kandidat yang akan dilabeli, tetapi sampel harus memuat juga CV dengan skor lexicon rendah (minimal 30% "Lainnya" dipilih acak). Tanpa ini, evaluasi menjadi sirkular terhadap lexicon.
- Catat jumlah per label dan bahasa tiap CV. Jika salah satu kelas sedikit, laporkan sebagai limitasi.
- Anonimkan data pribadi. CV asli tidak masuk repositori publik.

**Format `data/labels/labels.csv`:** `cv_id, source, language, label_a, label_b, label_final, notes` (tanpa nama orang).

## 11. Rencana Evaluasi

**Relevansi bertingkat** untuk role r: label = r bernilai 2, Fullstack bernilai 1, lainnya 0.

**Metrik utama:** nDCG@K (K = 5 dan 10), Precision@K (relevan = nilai ≥ 1), MRR, dan ROC-AUC (relevan vs tidak relevan, tidak bergantung pada ambang). Laporkan hasil per role dan per bahasa CV.

**Pembanding (baseline)**
- TF-IDF cosine dengan stopwords dwibahasa.
- Skor lexicon (jumlah skill role yang ditemukan).
- Acak (nilai harapan).

**Ablasi**
- Mode skor: `full` vs `chunk_max` vs `chunk_top3`.
- Panjang JD: hanya judul ("Backend Developer") vs template lengkap.
- Bahasa template: ID vs EN (korelasi Spearman antar peringkat dan overlap@5).
- Prototipe bilingual (stretch).

**Catatan statistik:** ukuran sampel kecil. Laporkan per CV bila perlu, jangan menggeneralisasi, dan cantumkan jumlah data tiap kelas. Hasil proxy kategori Kaggle sebelumnya (Precision@5 = 1,0 untuk JD Engineering dan 0,6 untuk Backend Developer) disimpan sebagai pelengkap, bukan metrik utama.

## 12. Risiko dan Limitasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Pemotongan 128 token | CV terbaca sebagian, peringkat berubah | Chunking + ablasi |
| Sedikit CV berlabel Frontend/Backend | Evaluasi lemah | Dataset lengkap, kontribusi tim, laporkan jumlah per kelas |
| Cakupan lexicon terbatas | Skill terlewat atau salah deteksi | Lexicon direview manusia, aturan batas kata, diperlakukan sebagai heuristik |
| Bias bahasa (CV Inggris vs Indonesia) | Peringkat condong ke bahasa tertentu | Uji language invariance, laporkan hasil per bahasa |
| Template terlalu mirip antar role | Sulit membedakan Frontend vs Backend | Uji sensitivitas, revisi template bila perlu |
| CV fullstack | Label ambigu | Kelas Fullstack dengan relevansi bertingkat |
| PDF scan atau layout kompleks | Teks kosong atau berantakan | Dilewati dan dilaporkan, OCR di luar scope |
| Skor dibaca sebagai persentase | Salah tafsir | Label "Skor kemiripan (relatif)" |
| Penggunaan untuk keputusan rekrutmen | Risiko bias dan diskriminasi | Posisikan sebagai alat bantu, bukan penyaring otomatis |

## 13. Tahapan Kerja

| Fase | Isi | Catatan |
|---|---|---|
| 0 | Revisi dokumen, draf template role dan lexicon | Selesai dengan dokumen ini |
| Paralel | Kumpulkan dan beri label 30–40 CV | Manual, dimulai sedini mungkin |
| 1 | Dropdown + `GET /roles` + prefill JD | Tidak bergantung pada skema skor |
| 2 | Chunking dan ablasi skema skor | Butuh label |
| 3 | Penjelasan v2 (skill, skill hilang, bukti) | Butuh lexicon |
| 4 | Evaluasi final dan baseline | Hasil masuk laporan |
| 5 | Polish, export CSV, proposal | |

## 14. Kriteria Sukses

- Pipeline end-to-end berjalan tanpa error untuk semua CV valid, dan file bermasalah dilewati dengan alasan jelas.
- Set berlabel minimal 30 CV, idealnya minimal 8 per kelas Frontend dan Backend (bila kurang, dicatat sebagai limitasi).
- Laporan evaluasi mencakup metrik utama, baseline, dan ablasi di atas, beserta limitasinya.
- Demo: role dipilih, CV diunggah, hasil muncul dalam waktu wajar setelah model termuat (target <10 detik untuk ±15 CV).

## 15. Keputusan Terbuka

1. Mode skor default (`full`, `chunk_max`, atau `chunk_top3`), ditentukan evaluasi.
2. Apakah prototipe bilingual (rata-rata embedding ID dan EN) dipakai.
3. Ukuran akhir set berlabel dan jumlah pelabel.
4. Apakah kolom skor per role (stretch) dimasukkan ke UI.