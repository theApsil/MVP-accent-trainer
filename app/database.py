from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "app.db"

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


REFERENCE_SAMPLES_DATA = [
    # th-звук
    ("thought", "TH AO T", "Межзубный /θ/ — кончик языка между зубами", "th_sound", "hard"),
    ("think", "TH IH NG K", "Глухой /θ/, не путать с /s/", "th_sound", "hard"),
    ("three", "TH R IY", "Сочетание /θr/ — сложное для русскоговорящих", "th_sound", "hard"),
    ("through", "TH R UW", "/θr/ + долгий /uː/", "th_sound", "hard"),
    ("thank", "TH AE NG K", "/θ/ в начале слова", "th_sound", "medium"),
    ("this", "DH IH S", "Звонкий /ð/ — голосовые связки работают", "th_sound", "hard"),
    ("that", "DH AE T", "Звонкий /ð/ + краткий /æ/", "th_sound", "hard"),
    ("they", "DH EY", "/ð/ + дифтонг /eɪ/", "th_sound", "medium"),
    ("them", "DH EH M", "Звонкий межзубный", "th_sound", "medium"),
    ("there", "DH EH R", "/ð/ + /eər/", "th_sound", "hard"),
    ("then", "DH EH N", "Звонкий /ð/ в начале", "th_sound", "medium"),
    ("though", "DH OW", "/ð/ + дифтонг /oʊ/", "th_sound", "hard"),
    # r-звук
    ("really", "R IH L IY", "Английский /r/ без вибрации", "r_sound", "medium"),
    ("right", "R AY T", "/r/ + дифтонг /aɪ/", "r_sound", "medium"),
    ("read", "R IY D", "/r/ перед долгим /iː/", "r_sound", "medium"),
    ("red", "R EH D", "/r/ + краткий /e/", "r_sound", "medium"),
    ("rock", "R AA K", "/r/ + /ɒ/", "r_sound", "medium"),
    ("rural", "R UH R AH L", "Двойной /r/ — самое сложное слово", "r_sound", "hard"),
    ("library", "L AY B R EH R IY", "/r/ в середине + конце", "r_sound", "hard"),
    ("February", "F EH B R UW EH R IY", "Два /r/ в одном слове", "r_sound", "hard"),
    ("world", "W ER L D", "Дифтонг /ɜːr/ + /l/", "r_sound", "hard"),
    ("girl", "G ER L", "/ɜːr/ + тёмный /l/", "r_sound", "hard"),
    ("work", "W ER K", "/ɜːr/ в закрытом слоге", "r_sound", "medium"),
    ("word", "W ER D", "Похоже на 'world', но без /l/", "r_sound", "medium"),
    ("car", "K AA R", "Долгий /ɑːr/", "r_sound", "easy"),
    ("far", "F AA R", "/ɑːr/ в конце слова", "r_sound", "easy"),
    ("bird", "B ER D", "/ɜːr/ + /d/", "r_sound", "medium"),
    ("third", "TH ER D", "/θ/ + /ɜːr/ + /d/ — двойная сложность", "r_sound", "hard"),
    # Гласные
    ("happy", "HH AE P IY", "Краткий /æ/ — открытая челюсть", "vowels", "medium"),
    ("apple", "AE P AH L", "/æ/ в начале + тёмный /l/", "vowels", "medium"),
    ("cat", "K AE T", "Классический /æ/", "vowels", "easy"),
    ("bad", "B AE D", "/æ/ между согласными", "vowels", "easy"),
    ("man", "M AE N", "/æ/ + носовой /n/", "vowels", "easy"),
    ("bed", "B EH D", "Краткий /e/", "vowels", "easy"),
    ("head", "HH EH D", "/e/ через 'ea'", "vowels", "easy"),
    ("said", "S EH D", "Исключение: 'said' читается как /sed/", "vowels", "medium"),
    ("ship", "SH IH P", "Краткий /ɪ/, не путать с /iː/", "vowels", "medium"),
    ("sheep", "SH IY P", "Долгий /iː/", "vowels", "medium"),
    ("live", "L IH V", "Глагол: краткий /ɪ/", "vowels", "medium"),
    ("leave", "L IY V", "Долгий /iː/", "vowels", "medium"),
    ("bit", "B IH T", "/ɪ/", "vowels", "easy"),
    ("beat", "B IY T", "/iː/", "vowels", "easy"),
    ("full", "F UH L", "Краткий /ʊ/", "vowels", "medium"),
    ("fool", "F UW L", "Долгий /uː/", "vowels", "medium"),
    ("book", "B UH K", "/ʊ/ в закрытом слоге", "vowels", "easy"),
    ("food", "F UW D", "/uː/", "vowels", "easy"),
    # Дифтонги
    ("time", "T AY M", "Дифтонг /aɪ/", "diphthongs", "easy"),
    ("nice", "N AY S", "/aɪ/ + /s/", "diphthongs", "easy"),
    ("buy", "B AY", "/aɪ/ в конце", "diphthongs", "easy"),
    ("now", "N AW", "Дифтонг /aʊ/", "diphthongs", "easy"),
    ("how", "HH AW", "/aʊ/", "diphthongs", "easy"),
    ("house", "HH AW S", "/aʊ/ + /s/", "diphthongs", "easy"),
    ("go", "G OW", "Дифтонг /oʊ/", "diphthongs", "easy"),
    ("no", "N OW", "/oʊ/ в конце", "diphthongs", "easy"),
    ("boat", "B OW T", "/oʊ/ + /t/", "diphthongs", "easy"),
    ("day", "D EY", "Дифтонг /eɪ/", "diphthongs", "easy"),
    ("say", "S EY", "/eɪ/ в конце", "diphthongs", "easy"),
    ("make", "M EY K", "/eɪ/ + /k/", "diphthongs", "easy"),
    ("boy", "B OY", "Дифтонг /ɔɪ/", "diphthongs", "easy"),
    ("toy", "T OY", "/ɔɪ/", "diphthongs", "easy"),
    ("voice", "V OY S", "/ɔɪ/ + /s/", "diphthongs", "medium"),
    # Сочетания согласных
    ("school", "S K UW L", "/sk/ + долгий /uː/ + тёмный /l/", "clusters", "medium"),
    ("street", "S T R IY T", "Сложный кластер /str/", "clusters", "hard"),
    ("strong", "S T R AO NG", "/str/ + /ɔː/ + /ŋ/", "clusters", "hard"),
    ("spring", "S P R IH NG", "/spr/ + /ŋ/", "clusters", "hard"),
    ("scream", "S K R IY M", "/skr/ + долгий /iː/", "clusters", "hard"),
    ("splash", "S P L AE SH", "/spl/ + /æ/ + /ʃ/", "clusters", "hard"),
    ("twelve", "T W EH L V", "Сложное окончание /lv/", "clusters", "hard"),
    ("twelfth", "T W EH L F TH", "Один из самых сложных кластеров", "clusters", "hard"),
    ("asked", "AE S K T", "Окончание /skt/", "clusters", "hard"),
    ("texts", "T EH K S T S", "Кластер /ksts/", "clusters", "hard"),
    # Шипящие и аффрикаты
    ("she", "SH IY", "/ʃ/ + /iː/", "sibilants", "easy"),
    ("show", "SH OW", "/ʃ/ + /oʊ/", "sibilants", "easy"),
    ("wash", "W AA SH", "/ʃ/ в конце", "sibilants", "medium"),
    ("measure", "M EH ZH ER", "Звонкий /ʒ/", "sibilants", "hard"),
    ("pleasure", "P L EH ZH ER", "/ʒ/ в середине", "sibilants", "hard"),
    ("vision", "V IH ZH AH N", "/ʒ/ через 'si'", "sibilants", "hard"),
    ("chair", "CH EH R", "Аффриката /tʃ/", "sibilants", "medium"),
    ("church", "CH ER CH", "Двойная /tʃ/", "sibilants", "hard"),
    ("watch", "W AA CH", "/tʃ/ в конце", "sibilants", "medium"),
    ("judge", "JH AH JH", "Двойная /dʒ/", "sibilants", "hard"),
    ("juice", "JH UW S", "/dʒ/ + /uː/", "sibilants", "medium"),
    # Многосложные
    ("computer", "K AH M P Y UW T ER", "Ударение на второй слог", "stress", "medium"),
    ("interesting", "IH N T R AH S T IH NG", "Безударные /ə/", "stress", "hard"),
    ("comfortable", "K AH M F ER T AH B AH L", "Произносится в 3 слога", "stress", "hard"),
    ("vegetable", "V EH JH T AH B AH L", "Редукция гласных", "stress", "hard"),
    ("temperature", "T EH M P R AH CH ER", "Сокращение в речи", "stress", "hard"),
    ("photography", "F AH T AA G R AH F IY", "Ударение на 2-й слог", "stress", "medium"),
    ("photograph", "F OW T AH G R AE F", "Ударение на 1-й слог", "stress", "medium"),
    ("development", "D IH V EH L AH P M AH N T", "Ударение на 2-й слог", "stress", "medium"),
    ("opportunity", "AA P ER T UW N AH T IY", "Ударение на 3-й слог", "stress", "medium"),
    ("necessary", "N EH S AH S EH R IY", "Ударение на 1-й слог", "stress", "medium"),
    # Базовые
    ("hello", "HH AH L OW", "Стандартное приветствие", "general", "easy"),
    ("world", "W ER L D", "Базовое слово", "general", "easy"),
    ("water", "W AO T ER", "Краткий /ɔː/ + /ər/", "general", "medium"),
    ("morning", "M AO R N IH NG", "/ɔːr/ + /ŋ/", "general", "easy"),
    ("evening", "IY V N IH NG", "Произносится в 2 слога", "general", "medium"),
    ("question", "K W EH S CH AH N", "/tʃ/ через 'ti'", "general", "medium"),
    ("answer", "AE N S ER", "'w' немое", "general", "easy"),
    ("language", "L AE NG G W AH JH", "/ŋg/ + /dʒ/", "general", "medium"),
    ("English", "IH NG G L IH SH", "/ŋg/ + /ʃ/", "general", "medium"),
    ("knowledge", "N AA L AH JH", "'k' немое", "general", "medium"),
    ("through", "TH R UW", "/θr/ + /uː/", "general", "hard"),
    ("though", "DH OW", "/ð/ + /oʊ/", "general", "medium"),
    ("thought", "TH AO T", "/θ/ + /ɔː/ + /t/", "general", "hard"),
    ("tough", "T AH F", "'ough' = /ʌf/", "general", "hard"),
]


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(engine)
    _seed_reference_samples()


def _seed_reference_samples() -> None:
    from app.models import ReferenceSample

    with SessionLocal() as session:
        existing_count = session.query(ReferenceSample).count()
        if existing_count >= len(REFERENCE_SAMPLES_DATA):
            return

        existing_words = {s.word for s in session.query(ReferenceSample).all()}
        added = 0
        for word, transcription, description, category, difficulty in REFERENCE_SAMPLES_DATA:
            if word in existing_words:
                continue
            session.add(ReferenceSample(
                word=word,
                transcription=transcription,
                audio_path=f"/static/reference_audio/{word}.wav",
                description=description,
                category=category,
                difficulty=difficulty,
            ))
            added += 1
        session.commit()
        if added:
            print(f"[DB] Добавлено {added} эталонов в базу")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()