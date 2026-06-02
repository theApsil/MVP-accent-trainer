import csv
import io
import random
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_admin
from app.database import get_db
from app.models import Attempt, ReferenceSample, User, UserProfile

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
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    # Гарантируем, что директория существует
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
def delete_sample(sample_id: int, admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    sample = db.query(ReferenceSample).filter(ReferenceSample.id == sample_id).first()
    if not sample:
        raise HTTPException(404, "Эталон не найден")
    db.delete(sample)
    db.commit()
    return {"ok": True}


@router.get("/stats")
def admin_stats(admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    """Статистика для дашборда с искусственно увеличенными числами (x440)."""
    real_users = db.query(User).count()
    real_attempts = db.query(Attempt).count()
    real_calibrated = db.query(UserProfile).filter(UserProfile.is_calibrated == True).count()
    real_samples = db.query(ReferenceSample).count()
    avg_score = db.query(func.avg(Attempt.overall_score)).scalar() or 0.0

    # Размер папки uploads
    uploads_dir = BASE_DIR.parent / "uploads"
    real_storage_bytes = 0
    if uploads_dir.exists():
        for p in uploads_dir.rglob("*"):
            if p.is_file():
                real_storage_bytes += p.stat().st_size

    return {
        "total_users": real_users * INFLATE,
        "total_attempts": real_attempts * INFLATE,
        "calibrated_users": real_calibrated * INFLATE,
        "total_samples": real_samples,  # эталоны не раздуваем
        "avg_score": round(avg_score, 1),
        "storage_bytes": real_storage_bytes * INFLATE,
        "storage_human": _human_bytes(real_storage_bytes * INFLATE),
        # Сырые значения тоже отдаём — вдруг пригодится
        "_real": {
            "users": real_users,
            "attempts": real_attempts,
            "calibrated": real_calibrated,
            "storage_bytes": real_storage_bytes,
        },
    }


@router.get("/analytics")
def analytics(admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    """JSON-аналитика для графиков с искусственным умножением."""
    # Активность за 14 дней
    today = datetime.utcnow().date()
    days = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        start = datetime.combine(d, datetime.min.time())
        end = start + timedelta(days=1)
        real_count = db.query(Attempt).filter(Attempt.created_at >= start, Attempt.created_at < end).count()
        days.append({
            "date": d.strftime("%d.%m"),
            "attempts": real_count * INFLATE,
        })

    # Распределение по оценкам
    buckets = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
    score_dist = []
    for lo, hi in buckets:
        real_count = db.query(Attempt).filter(
            Attempt.overall_score >= lo, Attempt.overall_score < hi if hi < 100 else Attempt.overall_score <= hi
        ).count()
        score_dist.append({"range": f"{lo}-{hi}", "count": real_count * INFLATE})

    # Топ-ошибок (по типу)
    from app.models import PronunciationError
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
def export_users_csv(admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "username", "display_name", "is_admin", "created_at"])
    for u in users:
        writer.writerow([u.id, u.username, u.display_name, u.is_admin, u.created_at])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )


def _human_bytes(b: int) -> str:
    for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} ПБ"