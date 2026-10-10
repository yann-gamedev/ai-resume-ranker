# AI Resume Ranker

Alat bantu untuk mengurutkan CV PDF/DOCX berdasarkan kemiripan semantik dengan job description (JD). Backend menggunakan FastAPI dan model multilingual Sentence Transformers; antarmuka menggunakan Streamlit. Skor adalah **kemiripan relatif**, bukan persentase kemampuan kandidat atau keputusan penerimaan.

## Menjalankan

Gunakan Python dengan dependensi yang tercantum di `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Di terminal lain, dari folder proyek yang sama:

```powershell
python -m streamlit run streamlit_app.py
```

Buka URL lokal yang ditampilkan Streamlit (umumnya `http://localhost:8501`). Backend menyediakan `GET /health`, `GET /roles`, dan `POST /rank`; dokumentasi API ada di `http://127.0.0.1:8000/docs`.

## Alur

1. Pilih role Backend atau Frontend dan bahasa template JD. Template diambil dari backend dan dapat diedit; mengganti role/bahasa akan menimpa edit JD.
2. Unggah satu atau beberapa CV PDF/DOCX, lalu klik **Ranking CV**.
3. Lihat skor, kata kunci yang sama antara CV dan JD, serta file yang dilewati. Kata kunci adalah overlap literal, **bukan** penjelasan skor embedding.

Saat ini ranking masih memakai mode `full`: model hanya membaca hingga 128 token awal pada masing-masing teks. Backend memperingatkan apabila JD melampaui 126 token. CV hasil scan tanpa teks tidak didukung; tidak ada OCR. Template dan daftar skill di `data/roles/roles.json` masih **draf** dan memerlukan tinjauan manusia. Fitur chunking dan penjelasan berbasis skill dalam `PRD.md` belum diimplementasikan.

## Struktur ringkas

- `app/`: ekstraksi, preprocessing, embedding, ranking, API, dan konfigurasi role.
- `streamlit_app.py`: antarmuka HTTP untuk backend.
- `data/roles/roles.json`: template JD dan draf lexicon.
- `evaluation/`: evaluasi eksperimental; hasil dari sampel kecil tidak boleh digeneralisasi.
- `PRD.md` dan `AGENT.md`: persyaratan serta aturan pengembangan.

CV sampel, dataset, dan teks debug lokal tidak disertakan dalam repositori demi privasi. Jika menjalankan `python app/extract.py`, tambahkan sendiri CV PDF/DOCX yang diizinkan ke `data/sample_cvs/` terlebih dahulu.
