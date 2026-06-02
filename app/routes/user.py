import io
import random
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.audio_processing import process_audio
from app.auth import get_current_user
from app.database import get_db
from app.models import Attempt, PronunciationError, PronunciationMatch, Task, UserProfile

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"

router = APIRouter()


SOUND_GROUPS = ["th", "r", "ae", "iy_ih", "stress", "clusters"]

TASK_TEMPLATES = {
    "th": [
        ("Тренировка межзубного /θ/", "Произнесите фразу с акцентом на 'th'", "I think three thousand things"),
        ("Звонкий /ð/", "Фокус на голосовых связках", "This, that, these and those"),
        ("Противопоставление /θ/ и /s/", "Разделяйте звуки чётко", "Sink and think, sing and thing"),
        ("Длинная фраза с 'th'", "Сохраняйте артикуляцию", "Thirty-three thieves thought thoughtfully"),
    ],
    "r": [
        ("Английский /r/ без вибрации", "Не катите 'р'", "Red roses really run"),
        ("/r/ в середине слова", "Плавный переход", "Library, February, very"),
        ("Сложное /ɜːr/", "Округлите губы", "World, girl, work, word"),
        ("/r/ и /l/ — не путать", "Чётко различайте", "Really lovely, lorry rally"),
    ],
    "ae": [
        ("Краткий /æ/", "Открытая челюсть", "The cat sat on the mat"),
        ("/æ/ vs /e/", "Опустите челюсть для /æ/", "Bad bed, man men, sat set"),
        ("/æ/ перед носовыми", "Не назализуйте чрезмерно", "Hand, sand, plan, ran"),
    ],
    "iy_ih": [
        ("Долгий /iː/ vs краткий /ɪ/", "Слушайте длительность", "Sheep ship, leave live, beat bit"),
        ("Долгий /iː/", "Растягивайте звук", "Please see these green trees"),
        ("Краткий /ɪ/", "Расслабьте мышцы", "Big little ship, fix it quick"),
    ],
    "stress": [
        ("Ударение в многосложных словах", "Выделите ударный слог", "Computer, important, develop"),
        ("Сдвиг ударения", "Сравните формы слова", "Photograph — photography — photographic"),
        ("Безударная редукция", "Слабые слоги — /ə/", "Comfortable, vegetable, interesting"),
    ],
    "clusters": [
        ("Сочетания /str/, /spr/", "Не вставляйте гласную", "Street, strong, spring, strange"),
        ("Окончание /-sts/, /-skts/", "Аккуратно с кластерами", "Texts, costs, lists, asked"),
        ("/tw/, /kw/, /sw/", "Чистые переходы", "Twelve quick swans"),
    ],
}


def _generate_tasks_for_user(username: str, weak_sounds: list[str], db: Session) -> int:
    """Создаёт задания на основе слабых звуков."""
    db.query(Task).filter(Task.username == username, Task.is_completed == False).delete()

    added = 0
    target_sounds = weak_sounds if weak_sounds else SOUND_GROUPS
    for sound in target_sounds:
        templates = TASK_TEMPLATES.get(sound, [])
        for title, desc, phrase in templates:
            difficulty = random.choice(["easy", "medium", "hard"])
            db.add(Task(
                username=username,
                title=title,
                description=desc,
                target_phrase=phrase,
                target_sounds=sound,
                difficulty=difficulty,
            ))
            added += 1

    if added < 10:
        for sound, templates in TASK_TEMPLATES.items():
            if sound in target_sounds:
                continue
            for title, desc, phrase in templates[:2]:
                db.add(Task(
                    username=username,
                    title=title,
                    description=desc,
                    target_phrase=phrase,
                    target_sounds=sound,
                    difficulty="easy",
                ))
                added += 1

    db.commit()
    return added


@router.post("/upload")
async def upload_audio(file: UploadFile = File(...),
                       user=Depends(get_current_user),
                       db: Session = Depends(get_db)):
    allowed = (".wav", ".mp3", ".m4a", ".ogg", ".webm", ".mp4")
    if not file.filename.lower().endswith(allowed):
        raise HTTPException(400, "Поддерживаются: wav, mp3, m4a, ogg, webm")

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
    for m in result["matches"]:
        db.add(PronunciationMatch(
            attempt_id=attempt.id, word=m["word"], note=m["note"],
        ))
    db.commit()

    return