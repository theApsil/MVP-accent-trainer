from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import authenticate, get_current_user
from app.database import get_db
from app.models import Attempt, ReferenceSample

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    if request.session.get("user"):
        user = request.session["user"]
        return RedirectResponse("/admin" if user["role"] == "admin" else "/dashboard", status_code=302)
    return RedirectResponse("/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    user = authenticate(username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Неверный логин или пароль"}
        )
    request.session["user"] = user
    return RedirectResponse("/admin" if user["role"] == "admin" else "/dashboard", status_code=302)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    attempts = (
        db.query(Attempt).filter(Attempt.username == user["username"])
        .order_by(Attempt.created_at.desc()).limit(10).all()
    )
    all_attempts = db.query(Attempt).filter(Attempt.username == user["username"]).all()
    avg_score = round(sum(a.overall_score for a in all_attempts) / len(all_attempts), 1) if all_attempts else 0
    scores_history = [round(a.overall_score, 1) for a in reversed(all_attempts[-10:])]

    return templates.TemplateResponse(
        "user_dashboard.html",
        {"request": request, "user": user, "attempts": attempts,
         "total_attempts": len(all_attempts), "avg_score": avg_score,
         "scores_history": scores_history},
    )


@router.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("upload.html", {"request": request, "user": user})


@router.get("/attempt/{attempt_id}", response_class=HTMLResponse)
def attempt_detail(attempt_id: int, request: Request,
                   user=Depends(get_current_user), db: Session = Depends(get_db)):
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt or attempt.username != user["username"]:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(
        "analysis_result.html",
        {"request": request, "user": user, "attempt": attempt},
    )


@router.get("/history", response_class=HTMLResponse)
def history(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    attempts = (
        db.query(Attempt).filter(Attempt.username == user["username"])
        .order_by(Attempt.created_at.desc()).all()
    )
    return templates.TemplateResponse(
        "history.html", {"request": request, "user": user, "attempts": attempts}
    )


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user or user["role"] != "admin":
        return RedirectResponse("/login", status_code=302)
    samples = db.query(ReferenceSample).order_by(ReferenceSample.created_at.desc()).all()
    attempts_count = db.query(Attempt).count()

    total_size = 0
    missing = []
    for s in samples:
        p = BASE_DIR.parent / s.audio_path.lstrip("/")
        if p.exists():
            total_size += p.stat().st_size
        else:
            missing.append(s.word)

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "user": user, "samples": samples,
         "attempts_count": attempts_count,
         "total_size_kb": round(total_size / 1024, 2),
         "missing": missing},
    )