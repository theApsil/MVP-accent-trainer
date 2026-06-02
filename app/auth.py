from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


USERS = {
    "user": {"password": "user", "role": "user", "display_name": "Danil Goncharuk", "handle": "d.goncharuk"},
    "admin": {"password": "admin", "role": "admin", "display_name": "Администратор", "handle": "admin"},
}


def authenticate(username: str, password: str) -> dict | None:
    u = USERS.get(username)
    if u and u["password"] == password:
        return {
            "username": username,
            "role": u["role"],
            "display_name": u["display_name"],
            "handle": u["handle"],
        }
    return None


def get_current_user(request: Request) -> dict:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Не авторизован")
    return user


def require_admin(request: Request) -> dict:
    user = get_current_user(request)
    if user["role"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Требуются права администратора")
    return user

def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    """Возвращает текущего пользователя или None (для публичных страниц)."""
    username = request.session.get("username")
    if not username:
        return None
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    return {
        "username": user.username,
        "display_name": user.display_name,
        "handle": user.username,
        "is_admin": user.is_admin,
    }


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Требует авторизации. Кидает 401, если не залогинен."""
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"Location": "/login"},
        )
    return user


def get_current_admin(request: Request, db: Session = Depends(get_db)):
    """Требует прав администратора."""
    user = get_current_user(request, db)
    if not user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для администратора",
        )
    return user