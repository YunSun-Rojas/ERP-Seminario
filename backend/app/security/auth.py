from datetime import datetime, timedelta, timezone
import bcrypt, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models import Usuario

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def hash_password(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()

def verify_password(p: str, h: str) -> bool:
    return bcrypt.checkpw(p.encode(), h.encode())

def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.SECRET_KEY, algorithm="HS256")

def get_current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> Usuario:
    err = HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales inválidas", {"WWW-Authenticate": "Bearer"})
    try:
        uid = int(jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise err
    user = db.get(Usuario, uid)
    if not user or not user.activo:
        raise err
    return user

def require_permission(codigo: str):
    def dep(user: Usuario = Depends(get_current_user)) -> Usuario:
        if user.role.nombre != "admin" and codigo not in {p.codigo for p in user.role.permisos}:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permiso insuficiente")
        return user
    return dep
