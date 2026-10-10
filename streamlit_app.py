"""Streamlit frontend for the resume-ranking HTTP API."""

import requests
import streamlit as st

BACKEND_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI-Based Resume Ranker", page_icon="📄", layout="wide")
st.title("AI-Based Resume Ranker")
st.caption("Bandingkan CV PDF/DOCX dengan satu job description melalui backend ranking.")

try:
    roles_response = requests.get(f"{BACKEND_BASE_URL}/roles", timeout=10)
    roles_response.raise_for_status()
    roles = roles_response.json()["roles"]
    if not roles:
        raise ValueError("Daftar role kosong")
except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as exc:
    st.error(f"Tidak dapat memuat role dari backend ({exc}). Pastikan backend berjalan di port 8000, lalu muat ulang halaman.")
    st.stop()

role_options = {item["id"]: item for item in roles}
role_ids = list(role_options)
role_id = st.selectbox(
    "Role target", role_ids, format_func=lambda value: role_options[value]["label"], key="selected_role"
)
language = st.radio(
    "Bahasa template", ("id", "en"),
    format_func=lambda value: "Indonesia" if value == "id" else "Inggris",
    horizontal=True, key="selected_language",
)
selection = (role_id, language)
if st.session_state.get("jd_template_selection") != selection:
    st.session_state["jd_text"] = role_options[role_id][f"template_{language}"]
    st.session_state["jd_template_selection"] = selection
jd_text = st.text_area("Job Description", height=180, key="jd_text")
st.caption("Mengganti role atau bahasa akan menimpa isi kotak JD.")
uploaded_files = st.file_uploader(
    "Unggah CV (PDF atau DOCX)", type=["pdf", "docx"], accept_multiple_files=True
)

if st.button("Ranking CV", type="primary"):
    if not jd_text.strip():
        st.error("Job Description tidak boleh kosong.")
    elif not uploaded_files:
        st.error("Unggah minimal satu file CV PDF atau DOCX.")
    else:
        multipart_files = [
            ("files", (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream"))
            for uploaded in uploaded_files
        ]
        try:
            with st.spinner("Memproses dan memeringkat CV..."):
                response = requests.post(
                    f"{BACKEND_BASE_URL}/rank",
                    data={"role": role_id, "jd_text": jd_text},
                    files=multipart_files,
                    timeout=180,
                )
        except requests.exceptions.ConnectionError:
            st.error("Tidak dapat terhubung ke backend. Pastikan uvicorn app.main:app --reload sudah berjalan di port 8000.")
        except requests.exceptions.RequestException as exc:
            st.error(f"Permintaan ke backend gagal: {exc}")
        else:
            if response.status_code == 400:
                try:
                    detail = response.json().get("detail", response.text)
                except ValueError:
                    detail = response.text
                st.error(f"Permintaan tidak valid: {detail}")
            elif not response.ok:
                st.error(f"Backend mengembalikan HTTP {response.status_code}: {response.text}")
            else:
                payload = response.json()
                for warning in payload.get("warnings", []):
                    st.warning(warning)
                st.subheader("Hasil ranking")
                ranking = payload.get("ranking", [])
                if ranking:
                    st.dataframe(
                        [
                            {
                                "filename": item["filename"],
                                "score": item["score"],
                                "kata_kunci_cocok": ", ".join(item.get("matched_keywords") or []) or "-",
                            }
                            for item in ranking
                        ],
                        column_config={
                            "score": st.column_config.NumberColumn("Skor kemiripan (relatif)", format="%.4f"),
                            "kata_kunci_cocok": st.column_config.TextColumn(
                                "Kata kunci yang sama di CV & JD"
                            )
                        },
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.caption(
                        "Skor dihitung dari kemiripan semantik keseluruhan teks (multibahasa); "
                        "kata kunci di atas hanya overlap literal sebagai petunjuk tambahan."
                    )
                else:
                    st.info("Tidak ada CV yang dapat diberi skor.")

                excluded = payload.get("excluded", [])
                if excluded:
                    st.subheader("File dilewati")
                    for item in excluded:
                        st.warning(f"{item['filename']}: {item['reason']}")

