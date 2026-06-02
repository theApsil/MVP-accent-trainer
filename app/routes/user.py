import io
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.audio_processing import process_audio
from app.auth import get_current_user
from app.database import get_db
from app.models import Attempt, PronunciationError

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"

router = APIRouter()


@router.post("/upload")
async def upload_audio(file: UploadFile = File(...),
                       user=Depends(get_current_user),
                       db: Session = Depends(get_db)):
    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".ogg", ".webm")):
        raise HTTPException(400, "Поддерживаются только аудиофайлы: wav, mp3, m4a, ogg, webm")

    raw_filename = f"{user['username']}_{file.filename}"
    raw_path = UPLOADS_DIR / raw_filename
    raw_path.write_bytes(await file.read())

    result = process_audio(raw_path, user["username"])

    attempt = Attempt(
        username=user["username"],
        original_filename=file.filename,
        audio_path=f"/uploads/{raw_filename}",
        cleaned_audio_path=result["cleaned_audio_path"],
        spectrogram_path=result["spectrogram_path"],
        recognized_text=result["recognized_text"],
        overall_score=result["overall_score"],
    )
    db.add(attempt)
    db.flush()

    for err in result["errors"]:
        db.add(PronunciationError(
            attempt_id=attempt.id, word=err["word"], error_type=err["error_type"],
            description=err["description"], reference_audio=err.get("reference_audio", ""),
            severity=err["severity"],
        ))
    db.commit()

    return {"attempt_id": attempt.id, "redirect": f"/attempt/{attempt.id}"}


@router.get("/export/{attempt_id}")
def export_pdf(attempt_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt or attempt.username != user["username"]:
        raise HTTPException(404, "Попытка не найдена")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"<b>Pronunciation Analysis Report #{attempt.id}</b>", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"User: {attempt.username}", styles["Normal"]),
        Paragraph(f"Date: {attempt.created_at:%Y-%m-%d %H:%M}", styles["Normal"]),
        Paragraph(f"File: {attempt.original_filename}", styles["Normal"]),
        Paragraph(f"Overall score: {attempt.overall_score:.1f} / 100", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"<b>Recognized text:</b>", styles["Heading2"]),
        Paragraph(attempt.recognized_text or "—", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"<b>Detected errors:</b>", styles["Heading2"]),
    ]
    for i, err in enumerate(attempt.errors, 1):
        story.append(Paragraph(
            f"<b>{i}. {err.word}</b> ({err.error_type}, severity: {err.severity})", styles["Normal"]
        ))
        story.append(Paragraph(err.description, styles["Normal"]))
        story.append(Spacer(1, 8))

    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{attempt.id}.pdf"},
    )