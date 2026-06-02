from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "app.db"

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(engine)
    _seed_reference_samples()


def _seed_reference_samples() -> None:
    from app.models import ReferenceSample

    with SessionLocal() as session:
        if session.query(ReferenceSample).count() > 0:
            return

        samples = [
            ReferenceSample(word="hello", transcription="HH AH L OW",
                            audio_path="/static/reference_audio/hello.wav",
                            description="Стандартное американское произношение"),
            ReferenceSample(word="world", transcription="W ER L D",
                            audio_path="/static/reference_audio/world.wav",
                            description="Особое внимание на дифтонг /ɜːr/"),
            ReferenceSample(word="thought", transcription="TH AO T",
                            audio_path="/static/reference_audio/thought.wav",
                            description="Межзубный /θ/ — кончик языка между зубами"),
            ReferenceSample(word="really", transcription="R IH L IY",
                            audio_path="/static/reference_audio/really.wav",
                            description="Английский /r/ без вибрации"),
            ReferenceSample(word="computer", transcription="K AH M P Y UW T ER",
                            audio_path="/static/reference_audio/computer.wav",
                            description="Ударение на второй слог"),
        ]
        session.add_all(samples)
        session.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()