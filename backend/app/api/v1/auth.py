from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Usuario
from backend.app.schemas.schemas import Token
from backend.app.security.auth import create_token, verify_password
from backend.app.services.audit import audit

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(Usuario).where(Usuario.username == form.username))
    if not user or not user.activo or not verify_password(form.password, user.password_hash):
        audit(db, user.id if user else None, "LOGIN", "auth", form.username, "FALLO"); db.commit()
        raise HTTPException(401, "Usuario o contraseña incorrectos")
    audit(db, user.id, "LOGIN", "auth", user.username); db.commit()
    return Token(access_token=create_token(user.id))
