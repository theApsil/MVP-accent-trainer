from fastapi import HTTPException, Request, status

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


def get_current_user_optional(request: Request) -> dict | None:
    """Возвращает пользователя из сессии или None (для публичных страниц)."""
    return request.session.get("user")


def get_current_user(request: Request) -> dict:
    """Требует авторизации. Кидает 401, если не залогинен."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Не авторизован")
    return user


def require_admin(request: Request) -> dict:
    """Требует прав администратора."""
    user = get_current_user(request)
    if user["role"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Требуются права администратора")
    return user