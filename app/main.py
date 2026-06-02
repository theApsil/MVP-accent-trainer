from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.database import init_db
from app.routes import admin, pages, user

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Accent Analyzer MVP")
app.add_middleware(SessionMiddleware, secret_key="dev-secret-key-change-me")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/uploads", StaticFiles(directory=BASE_DIR / "uploads"), name="uploads")
app.include_router(pages.router)
app.include_router(user.router, prefix="/api/user", tags=["user"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.on_event("startup")
def on_startup() -> None:
    (BASE_DIR / "uploads").mkdir(exist_ok=True)
    (BASE_DIR / "data").mkdir(exist_ok=True)
    (BASE_DIR / "static" / "reference_audio").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "static" / "spectrograms").mkdir(parents=True, exist_ok=True)
    init_db()