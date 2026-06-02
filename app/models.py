from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
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


class ReferenceSample(Base):
    __tablename__ = "reference_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    word: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    transcription: Mapped[str] = mapped_column(String(256))
    audio_path: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)