from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import Attempt, ReferenceSample

BASE_DIR = Path(__file__).resolve().parent.parent
REFERENCE_DIR = BASE_DIR / "static" / "reference_audio"

router = APIRouter()


@router.post("/samples")
async def create_sample(word: str = Form(...), transcription: str = Form(...),
                        description: str = Form(""), file: UploadFile = File(...),
                        user=Depends(require_admin), db: Session = Depends(get_db)):
    safe_word = word.strip().lower().replace(" ", "_")
    audio_filename = f"{safe_word}.wav"
    audio_path = REFERENCE_DIR / audio_filename
    audio_path.write_bytes(await file.read())

    existing = db.query(ReferenceSample).filter(ReferenceSample.word == safe_word).first()
    if existing:
        existing.transcription = transcription
        existing.description = description
        existing.audio_path = f"/static/reference_audio/{audio_filename}"
    else:
        db.add(ReferenceSample(
            word=safe_word, transcription=transcription, description=description,
            audio_path=f"/static/reference_audio/{audio_filename}",
        ))
    db.commit()
    return RedirectResponse("/admin", status_code=302)


@router.post("/samples/{sample_id}/delete")
def delete_sample(sample_id: int, user=Depends(require_admin), db: Session = Depends(get_db)):
    sample = db.query(ReferenceSample).filter(ReferenceSample.id == sample_id).first()
    if not sample:
        raise HTTPException(404, "Не найдено")
    db.delete(sample)
    db.commit()
    return RedirectResponse("/admin", status_code=302)


@router.get("/status")
def status(user=Depends(require_admin), db: Session = Depends(get_db)):
    samples = db.query(ReferenceSample).all()
    total_size = 0
    missing = []
    for s in samples:
        p = BASE_DIR.parent / s.audio_path.lstrip("/")
        if p.exists():
            total_size += p.stat().st_size
        else:
            missing.append(s.word)
    return {
        "samples_count": len(samples),
        "total_size_kb": round(total_size / 1024, 2),
        "missing_files": missing,
        "attempts_total": db.query(Attempt).count(),
    }