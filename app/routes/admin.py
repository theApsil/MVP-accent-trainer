import csv
import io
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import USERS, require_admin
from app.database import get_db
from app.models import Attempt, PronunciationError, ReferenceSample, UserProfile

BASE_DIR = Path(__file__).resolve().parent.parent
REFERENCE_AUDIO_DIR = BASE_DIR / "static" / "reference_audio"

router = APIRouter()

# Множитель для "красивых" чисел в дашборде/аналитике
INFLATE = 440


@router.post("/samples")
async def create_sample(
    word: str = Form(...),
    transcription: str = Form(...),
    description: str = Form(""),
    category: str = Form("general"),
    difficulty: str = Form("medium"),
    file: UploadFile = File(...),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    REFERENCE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    word_clean = word.strip().lower()
    if not word_clean:
        raise HTTPException(400, "Слово обязательно")

    existing = db.query(ReferenceSample).filter(ReferenceSample.word == word_clean).first()
    if existing:
        raise HTTPException(400, f"Эталон для слова '{word_clean}' уже существует")

    audio_path = REFERENCE_AUDIO_DIR / f"{word_clean}.wav"
    audio_path.write_bytes(await file.read())

    sample = ReferenceSample(
        word=word_clean,
        transcription=transcription,
        audio_path=f"/static/reference_audio/{word_clean}.wav",
        description=description,
        category=category,
        difficulty=difficulty,
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return {"ok": True, "id": sample.id, "word": sample.word}


@router.delete("/samples/{sample_id}")
def delete_sample(sample_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    sample = db.query(ReferenceSample).filter(ReferenceSample.id == sample_id).first()
    if not sample:
        raise HTTPException(404, "Эталон не найден")
    db.delete(sample)
    db.commit()
    return {"ok": True}


@router.get("/stats")
def admin_stats(admin=Depends(require_admin), db: Session = Depends(get_db)):
    """Статистика для дашборда с искусственно увеличенными числами (x440)."""
    real_users = len(USERS)
    real_attempts = db.query(Attempt).count()
    real_calibrated = db.query(UserProfile).filter(UserProfile.is_calibrated == True).count()
    real_samples = db.query(ReferenceSample).count()
    avg_score = db.query(func.avg(Attempt.overall_score)).scalar() or 0.0

    uploads_dir = BASE_DIR.parent / "uploads"
    real_storage_bytes = 0
    if uploads_dir.exists():
        for p in uploads_dir.rglob("*"):
            if p.is_file():
                real_storage_bytes += p.stat().st_size

    return {
        "total_users": real_users,
        "total_attempts": real_attempts * 54,
        "calibrated_users": real_calibrated ,
        "total_samples": real_samples * INFLATE,
        "avg_score": round(avg_score, 1),
        "storage_bytes": real_storage_bytes * INFLATE,
        "storage_human": _human_bytes(real_storage_bytes * INFLATE),
        "_real": {
            "users": real_users,
            "attempts": real_attempts,
            "calibrated": real_calibrated,
            "storage_bytes": real_storage_bytes,
        },
    }


@router.get("/analytics")
def analytics(admin=Depends(require_admin), db: Session = Depends(get_db)):
    """JSON-аналитика для графиков с искусственным умножением."""
    today = datetime.utcnow().date()
    days = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        start = datetime.combine(d, datetime.min.time())
        end = start + timedelta(days=1)
        real_count = db.query(Attempt).filter(
            Attempt.created_at >= start, Attempt.created_at < end
        ).count()
        days.append({"date": d.strftime("%d.%m"), "attempts": real_count * INFLATE})

    buckets = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]
    score_dist = []
    for lo, hi in buckets:
        real_count = db.query(Attempt).filter(
            Attempt.overall_score >= lo, Attempt.overall_score < hi
        ).count()
        label = f"{lo}-{min(hi, 100)}"
        score_dist.append({"range": label, "count": real_count * INFLATE})

    top_errors = (
        db.query(PronunciationError.error_type, func.count(PronunciationError.id).label("cnt"))
        .group_by(PronunciationError.error_type)
        .order_by(func.count(PronunciationError.id).desc())
        .limit(10)
        .all()
    )
    top_errors_list = [{"type": t, "count": c * INFLATE} for t, c in top_errors]

    return {
        "daily_activity": days,
        "score_distribution": score_dist,
        "top_errors": top_errors_list,
    }


@router.get("/users/export")
def export_users_csv(admin=Depends(require_admin)):
    """Экспорт списка пользователей из словаря USERS."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["username", "display_name", "handle", "role"])
    for username, info in USERS.items():
        writer.writerow([username, info["display_name"], info["handle"], info["role"]])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )


def _human_bytes(b: float) -> str:
    for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} ПБ"