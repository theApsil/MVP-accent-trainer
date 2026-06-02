from datetime import datetime

from fastapi import APIRouter, Depends, Request, HTTPException, File, UploadFile, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_current_user_optional, get_current_user, get_current_admin
from app.database import get_db
from app.models import Attempt, ReferenceSample, Task, User, UserProfile

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, user=None, **extra):
    return {"request": request, "user": user, **extra}


@router.get("/", response_class=HTMLResponse)
def index(request: Request, user=Depends(get_current_user_optional)):
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", _ctx(request))


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user=Depends(get_current_user_optional)):
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", _ctx(request))


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    difficulty: str | None = None,
    sound: str | None = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.username == user["username"]).first()
    if not profile or not profile.is_calibrated:
        return RedirectResponse("/calibrate", status_code=302)

    attempts = (
        db.query(Attempt)
        .filter(Attempt.username == user["username"])
        .order_by(Attempt.created_at.desc())
        .limit(20)
        .all()
    )

    tasks_q = db.query(Task).filter(Task.username == user["username"], Task.is_completed == False)
    if difficulty and difficulty in ("easy", "medium", "hard"):
        tasks_q = tasks_q.filter(Task.difficulty == difficulty)
    if sound:
        tasks_q = tasks_q.filter(Task.target_sounds == sound)
    tasks = tasks_q.order_by(Task.created_at.desc()).all()

    # Уникальные звуки для фильтра
    all_sounds = (
        db.query(Task.target_sounds)
        .filter(Task.username == user["username"])
        .distinct()
        .all()
    )
    sound_options = sorted({s[0] for s in all_sounds if s[0]})

    weak_sounds = profile.weak_sounds.split(",") if profile.weak_sounds else []

    return templates.TemplateResponse(
        "dashboard.html",
        _ctx(
            request,
            user=user,
            attempts=attempts,
            tasks=tasks,
            profile=profile,
            weak_sounds=weak_sounds,
            sound_options=sound_options,
            filter_difficulty=difficulty or "",
            filter_sound=sound or "",
        ),
    )


@router.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.username == user["username"]).first()
    if not profile or not profile.is_calibrated:
        return RedirectResponse("/calibrate", status_code=302)
    return templates.TemplateResponse("upload.html", _ctx(request, user=user))


@router.get("/calibrate", response_class=HTMLResponse)
def calibrate_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("calibrate.html", _ctx(request, user=user))


@router.get("/attempt/{attempt_id}", response_class=HTMLResponse)
def attempt_page(attempt_id: int, request: Request,
                 user=Depends(get_current_user), db: Session = Depends(get_db)):
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt or attempt.username != user["username"]:
        raise HTTPException(404, "Попытка не найдена")
    return templates.TemplateResponse("analysis_result.html", _ctx(request, user=user, attempt=attempt))


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request,
                    admin=Depends(get_current_admin),
                    db: Session = Depends(get_db)):
    samples = db.query(ReferenceSample).order_by(ReferenceSample.created_at.desc()).all()
    users = db.query(User).order_by(User.created_at.desc()).all()
    attempts = db.query(Attempt).order_by(Attempt.created_at.desc()).limit(50).all()
    return templates.TemplateResponse(
        "admin_dashboard.html",
        _ctx(request, user=admin, samples=samples, users=users, attempts=attempts),
    )