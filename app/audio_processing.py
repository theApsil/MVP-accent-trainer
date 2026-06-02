import random
import warnings
from pathlib import Path

import librosa
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR.parent / "uploads"
SPECTROGRAMS_DIR = BASE_DIR / "static" / "spectrograms"
SPECTROGRAMS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Симулированные эталоны для "распознавания"
SAMPLE_PHRASES = [
    "the quick brown fox jumps over the lazy dog",
    "i think this is really interesting and important",
    "she sells seashells by the seashore",
    "how much wood would a woodchuck chuck",
    "peter piper picked a peck of pickled peppers",
    "the rain in spain stays mainly in the plain",
    "world peace through global cooperation",
    "three thousand thoughtful thinkers",
    "red leather yellow leather",
    "unique new york",
]

ERROR_TEMPLATES = [
    {"word": "think", "type": "th_sound", "desc": "Звук /θ/ заменён на /s/ или /t/. Кончик языка должен быть между зубами.", "severity": "high"},
    {"word": "world", "type": "r_sound", "desc": "Раскатистый русский /р/ вместо мягкого английского /r/. Не катите язык.", "severity": "high"},
    {"word": "very", "type": "v_sound", "desc": "Звук /v/ заменён на /w/. Прижмите нижнюю губу к верхним зубам.", "severity": "medium"},
    {"word": "cat", "type": "ae_sound", "desc": "Краткий /æ/ произнесён как /e/. Опустите челюсть ниже.", "severity": "medium"},
    {"word": "ship", "type": "iy_ih", "desc": "Долгий /iː/ вместо краткого /ɪ/. Расслабьте мышцы.", "severity": "low"},
    {"word": "interesting", "type": "stress", "desc": "Ударение на втором слоге вместо первого.", "severity": "medium"},
    {"word": "three", "type": "th_sound", "desc": "Звонкая замена /θ/. Должно быть глухо.", "severity": "high"},
    {"word": "girl", "type": "r_sound", "desc": "Жёсткий /р/ вместо /ɜːr/. Округлите губы.", "severity": "high"},
]

MATCH_TEMPLATES = [
    {"word": "the", "note": "Артикль произнесён корректно"},
    {"word": "and", "note": "Сочетание звуков верное"},
    {"word": "is", "note": "Краткая форма /ɪz/ — чисто"},
    {"word": "this", "note": "Звонкий /ð/ хорошо слышен"},
    {"word": "really", "note": "Звук /r/ мягкий, без вибрации"},
    {"word": "important", "note": "Ударение поставлено верно"},
    {"word": "people", "note": "/p/ с придыханием, как надо"},
]


def _load_audio(input_path: Path):
    """Загрузка аудио с фолбэком через ffmpeg/audioread."""
    try:
        y, sr = sf.read(str(input_path))
        if y.ndim > 1:
            y = y.mean(axis=1)
        if sr != 16000:
            y = librosa.resample(y.astype(np.float32), orig_sr=sr, target_sr=16000)
            sr = 16000
        return y.astype(np.float32), sr
    except Exception:
        y, sr = librosa.load(str(input_path), sr=16000, mono=True)
        return y, sr


def _save_spectrogram(y, sr, out_path: Path) -> None:
    plt.figure(figsize=(10, 4), facecolor="#0a0a0f")
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    S_dB = librosa.power_to_db(S, ref=np.max)
    librosa.display.specshow(S_dB, sr=sr, x_axis="time", y_axis="mel", cmap="magma")
    plt.colorbar(format="%+2.0f dB")
    plt.title("Mel-Spectrogram", color="white")
    plt.gca().set_facecolor("#0a0a0f")
    plt.tick_params(colors="white")
    plt.tight_layout()
    plt.savefig(str(out_path), facecolor="#0a0a0f", dpi=100)
    plt.close()


def _normalize(y: np.ndarray) -> np.ndarray:
    peak = np.max(np.abs(y)) if len(y) else 1.0
    if peak < 1e-6:
        return y
    return (y / peak) * 0.95


def process_audio(input_path: Path, username: str) -> dict:
    """Обрабатывает аудио и возвращает словарь с результатами анализа."""
    # 1. Загрузка
    y, sr = _load_audio(input_path)

    # 2. Нормализация (упрощённое "шумоподавление")
    y_clean = _normalize(y)

    # 3. Сохранение очищенного аудио
    cleaned_name = f"{username}_cleaned_{random.randint(1000, 9999)}.wav"
    cleaned_path = UPLOADS_DIR / cleaned_name
    sf.write(str(cleaned_path), y_clean, sr)

    # 4. Спектрограмма
    spec_name = f"{username}_spec_{random.randint(1000, 9999)}.png"
    spec_path = SPECTROGRAMS_DIR / spec_name
    _save_spectrogram(y_clean, sr, spec_path)

    # 5. "Распознавание" — выбираем случайную фразу
    recognized_text = random.choice(SAMPLE_PHRASES)

    # 6. Генерация ошибок и совпадений
    num_errors = random.randint(1, 4)
    errors = []
    for err in random.sample(ERROR_TEMPLATES, k=min(num_errors, len(ERROR_TEMPLATES))):
        errors.append({
            "word": err["word"],
            "error_type": err["type"],
            "description": err["desc"],
            "severity": err["severity"],
            "reference_audio": f"/static/reference_audio/{err['word']}.wav",
        })

    num_matches = random.randint(2, 5)
    matches = []
    for m in random.sample(MATCH_TEMPLATES, k=min(num_matches, len(MATCH_TEMPLATES))):
        matches.append({"word": m["word"], "note": m["note"]})

    # 7. Общая оценка
    base_score = random.uniform(55, 95)
    penalty = sum(
        {"high": 8, "medium": 4, "low": 2}[e["severity"]] for e in errors
    )
    overall_score = max(20.0, min(100.0, base_score - penalty + len(matches) * 1.5))

    return {
        "cleaned_audio_path": f"/uploads/{cleaned_name}",
        "spectrogram_path": f"/static/spectrograms/{spec_name}",
        "recognized_text": recognized_text,
        "overall_score": round(overall_score, 1),
        "errors": errors,
        "matches": matches,
    }