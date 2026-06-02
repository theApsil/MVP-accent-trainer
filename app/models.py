from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    audio_path: Mapped[str] = mapped_column(String(512))
    cleaned_audio_path: Mapped[str] = mapped_column(String(512))
    spectrogram_path: Mapped[str] = mapped_column(String(512))
    recognized_text: Mapped[str] = mapped_column(Text, default="")
    overall_score: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    errors: Mapped[list["PronunciationError"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )
    matches: Mapped[list["PronunciationMatch"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )


class PronunciationError(Base):
    __tablename__ = "pronunciation_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id"))
    word: Mapped[str] = mapped_column(String(128))
    error_type: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text)
    reference_audio: Mapped[str] = mapped_column(String(512), default="")
    severity: Mapped[str] = mapped_column(String(16), default="medium")

    attempt: Mapped[Attempt] = relationship(back_populates="errors")


class PronunciationMatch(Base):
    """Слова, произнесённые верно (для мотивации)."""
    __tablename__ = "pronunciation_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id"))
    word: Mapped[str] = mapped_column(String(128))
    note: Mapped[str] = mapped_column(Text, default="Произношение совпало с эталоном")

    attempt: Mapped[Attempt] = relationship(back_populates="matches")


class ReferenceSample(Base):
    __tablename__ = "reference_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    word: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    transcription: Mapped[str] = mapped_column(String(256))
    audio_path: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(64), default="general")
    difficulty: Mapped[str] = mapped_column(String(16), default="medium")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserProfile(Base):
    """Профиль пользователя: калибровка + слабые звуки."""
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    is_calibrated: Mapped[bool] = mapped_column(Boolean, default=False)
    calibration_audio: Mapped[str] = mapped_column(String(512), default="")
    weak_sounds: Mapped[str] = mapped_column(Text, default="")  # CSV: "th,r,æ"
    avg_pitch: Mapped[float] = mapped_column(Float, default=0.0)
    speech_rate: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Task(Base):
    """Персонализированные задания для пользователя."""
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    target_phrase: Mapped[str] = mapped_column(String(512))
    target_sounds: Mapped[str] = mapped_column(String(128), default="")
    difficulty: Mapped[str] = mapped_column(String(16), default="medium")
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)