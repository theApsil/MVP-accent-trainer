from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import authenticate, get_current_user
from app.database import get_db
from app.models import Attempt, ReferenceSample, Task, UserProfile

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
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    user = authenticate(username, password)
    if not user:
        return templates.TemplateResponse(
            request, "login.html", {"error": "Неверный логин или пароль"}
        )
    request.session["user"] = user
    if user["role"] == "admin":
        return RedirectResponse("/admin", status_code=302)

    with next(get_db()) as db:
        profile = db.query(UserProfile).filter(UserProfile.username == username).first()
        if not profile or not profile.is_calibrated:
            return RedirectResponse("/calibrate", status_code=302)
    return RedirectResponse("/dashboard", status_code=302)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


@router.get("/calibrate", response_class=HTMLResponse)
def calibrate_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse(request, "calibrate.html", {"user": user})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.username == user["username"]).first()
    if not profile or not profile.is_calibrated:
        return RedirectResponse("/calibrate", status_code=302)

    attempts = (
        db.query(Attempt).filter(Attempt.username == user["username"])
        .order_by(Attempt.created_at.desc()).limit(10).all()
    )
    all_attempts = db.query(Attempt).filter(Attempt.username == user["username"]).all()
    avg_score = round(sum(a.overall_score for a in all_attempts) / len(all_attempts), 1) if all_attempts else 0
    scores_history = [round(a.overall_score, 1) for a in reversed(all_attempts[-10:])]

    tasks = (
        db.query(Task).filter(Task.username == user["username"], Task.is_completed == False)
        .order_by(Task.created_at.desc()).limit(6).all()
    )

    return templates.TemplateResponse(
        request,
        "user_dashboard.html",
        {
            "user": user, "attempts": attempts,
            "total_attempts": len(all_attempts), "avg_score": avg_score,
            "scores_history": scores_history,
            "profile": profile,
            "tasks": tasks,
            "weak_sounds": profile.weak_sounds.split(",") if profile.weak_sounds else [],
        },
    )


@router.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.username == user["username"]).order_by(Task.created_at.desc()).all()
    return templates.TemplateResponse(request, "tasks.html", {"user": user, "tasks": tasks})


@router.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse(request, "upload.html", {"user": user})


@router.get("/attempt/{attempt_id}", response_class=HTMLResponse)
def attempt_detail(attempt_id: int, request: Request,
                   user=Depends(get_current_user), db: Session = Depends(get_db)):
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt or attempt.username != user["username"]:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(
        request, "analysis_result.html", {"user": user, "attempt": attempt}
    )


@router.get("/history", response_class=HTMLResponse)
def history(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    attempts = (
        db.query(Attempt).filter(Attempt.username == user["username"])
        .order_by(Attempt.created_at.desc()).all()
    )
    return templates.TemplateResponse(
        request, "history.html", {"user": user, "attempts": attempts}
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
        request,
        "admin_dashboard.html",
        {
            "user": user, "samples": samples,
            "attempts_count": attempts_count,
            "total_size_kb": round(total_size / 1024, 2),
            "missing": missing,
        },
    )