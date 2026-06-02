import random
import uuid
from pathlib import Path

import librosa
import librosa.display
import matplotlib
import noisereduce as nr
import numpy as np
import soundfile as sf

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent
SPECTROGRAMS_DIR = BASE_DIR / "static" / "spectrograms"
UPLOADS_DIR = BASE_DIR / "uploads"

FAKE_ERRORS_POOL = [
    {"word": "thought", "error_type": "consonant",
     "description": "Звук /θ/ произнесён как /s/ или /t/. Кончик языка должен слегка касаться верхних зубов.",
     "severity": "high"},
    {"word": "world", "error_type": "vowel",
     "description": "Дифтонг /ɜːr/ произнесён слишком открыто. Требуется округление губ при артикуляции.",
     "severity": "medium"},
    {"word": "really", "error_type": "consonant",
     "description": "Звук /r/ произнесён как русский раскатистый. В английском /r/ — апикальный, без вибрации.",
     "severity": "high"},
    {"word": "happy", "error_type": "vowel",
     "description": "Краткий /æ/ заменён на /e/. Требуется более открытая артикуляция и опущенная челюсть.",
     "severity": "medium"},
    {"word": "computer", "error_type": "stress",
     "description": "Ударение поставлено на первый слог. Правильно: com-PU-ter.",
     "severity": "low"},
    {"word": "interesting", "error_type": "intonation",
     "description": "Безударные гласные не редуцированы до /ə/.",
     "severity": "low"},
]


def process_audio(input_path: Path, username: str) -> dict:
    uid = uuid.uuid4().hex[:12]

    y, sr = librosa.load(str(input_path), sr=16000, mono=True)
    y_clean = nr.reduce_noise(y=y, sr=sr, prop_decrease=0.85)

    peak = np.max(np.abs(y_clean))
    if peak > 0:
        y_clean = y_clean / peak * 0.95

    cleaned_filename = f"{username}_{uid}_cleaned.wav"
    cleaned_path = UPLOADS_DIR / cleaned_filename
    sf.write(str(cleaned_path), y_clean, sr)

    spec_filename = f"{username}_{uid}_spec.png"
    spec_path = SPECTROGRAMS_DIR / spec_filename
    _generate_spectrogram(y_clean, sr, spec_path)

    recognized_text = _recognize_text(cleaned_path)
    errors = _analyze_errors(recognized_text)
    overall_score = _calculate_score(errors)

    return {
        "cleaned_audio_path": f"/uploads/{cleaned_filename}",
        "spectrogram_path": f"/static/spectrograms/{spec_filename}",
        "recognized_text": recognized_text,
        "errors": errors,
        "overall_score": overall_score,
    }


def _generate_spectrogram(y: np.ndarray, sr: int, output_path: Path) -> None:
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(12, 4), facecolor="#0f0f1e")
    ax.set_facecolor("#0f0f1e")

    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    S_db = librosa.power_to_db(S, ref=np.max)
    img = librosa.display.specshow(
        S_db, sr=sr, x_axis="time", y_axis="mel", fmax=8000, ax=ax, cmap="magma"
    )
    cbar = fig.colorbar(img, ax=ax, format="%+2.0f dB")
    cbar.ax.tick_params(colors="#a0a0c0")
    ax.set_title("Мел-спектрограмма речи", color="#e0e0ff", fontsize=14, pad=15)
    ax.tick_params(colors="#a0a0c0")
    ax.xaxis.label.set_color("#a0a0c0")
    ax.yaxis.label.set_color("#a0a0c0")
    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight", facecolor="#0f0f1e")
    plt.close(fig)


def _recognize_text(audio_path: Path) -> str:
    try:
        from faster_whisper import WhisperModel
        global _whisper_model
        if "_whisper_model" not in globals():
            _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = _whisper_model.transcribe(str(audio_path), language="en", beam_size=1)
        text = " ".join(seg.text.strip() for seg in segments)
        return text or "Hello, this is my pronunciation test."
    except Exception as e:
        print(f"[WARN] Whisper unavailable, using stub: {e}")
        return "Hello, I think the weather is really interesting today."


def _analyze_errors(recognized_text: str) -> list[dict]:
    words_in_text = recognized_text.lower().split()
    matched = [e.copy() for e in FAKE_ERRORS_POOL if e["word"] in words_in_text]
    if not matched:
        matched = [e.copy() for e in random.sample(FAKE_ERRORS_POOL, k=random.randint(2, 3))]
    for err in matched:
        err["reference_audio"] = f"/static/reference_audio/{err['word']}.wav"
    return matched[:4]


def _calculate_score(errors: list[dict]) -> float:
    weights = {"high": 15, "medium": 8, "low": 3}
    penalty = sum(weights.get(e["severity"], 5) for e in errors)
    return max(40.0, min(100.0, 100.0 - penalty + random.uniform(-5, 5)))