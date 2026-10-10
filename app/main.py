"""FastAPI endpoints for health checks and resume ranking."""

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.embed import _model
from app.extract import extract_text
from app.explain import get_matched_keywords
from app.preprocess import preprocess
from app.rank import rank_resumes
from app.roles import get_roles, is_valid_role

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/roles")
def roles():
    """Return validated role labels and bilingual templates."""
    return {"roles": get_roles()}


@app.post("/rank")
async def rank(
    jd_text: str | None = Form(default=None),
    files: list[UploadFile] | None = File(default=None),
    role: str | None = Form(default=None),
):
    """Rank uploaded CVs against a text JD, reporting rejected files separately."""
    if not is_valid_role(role):
        raise HTTPException(status_code=400, detail="role wajib diisi: frontend atau backend")
    if not jd_text or not jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text wajib diisi dan tidak boleh kosong")
    if not files:
        raise HTTPException(status_code=400, detail="Minimal satu file CV harus diunggah")
    token_count = len(_model.tokenizer.encode(jd_text, add_special_tokens=True, truncation=False))
    warnings = []
    if token_count > 126:
        warnings.append("JD melebihi 126 token; bagian akhir tidak terbaca model.")

    cv_texts = {}
    excluded = []
    for upload in files:
        filename = upload.filename or "unnamed"
        temp_path = None
        try:
            suffix = Path(filename).suffix.lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary:
                temp_path = temporary.name
                while chunk := await upload.read(1024 * 1024):
                    temporary.write(chunk)
            cv_texts[filename] = extract_text(temp_path)
        except Exception as exc:
            excluded.append({"filename": filename, "reason": str(exc)})
        finally:
            await upload.close()
            if temp_path is not None:
                os.unlink(temp_path)

    ranking, skipped_files = rank_resumes(jd_text, cv_texts)
    excluded.extend({"filename": filename, "reason": reason} for filename, reason in skipped_files)
    jd_clean = preprocess(jd_text)
    return {
        "role": role,
        "warnings": warnings,
        "ranking": [
            {
                "filename": filename,
                "score": score,
                "matched_keywords": get_matched_keywords(jd_clean, preprocess(cv_texts[filename])),
            }
            for filename, score in ranking
        ],
        "excluded": excluded,
    }
