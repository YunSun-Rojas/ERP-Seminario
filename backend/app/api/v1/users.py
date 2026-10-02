from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Role, Usuario
from backend.app.schemas.schemas import UsuarioIn, UsuarioOut
from backend.app.security.auth import get_current_user, hash_password, require_permission
from backend.app.services.audit import audit

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UsuarioOut)
def me(user=Depends(get_current_user)):
    return user

@router.get("", response_model=list[UsuarioOut])
def list_users(db: Session = Depends(get_db), _=Depends(require_permission("usuarios:leer"))):
    return db.scalars(select(Usuario).order_by(Usuario.username)).all()

@router.post("", response_model=UsuarioOut, status_code=201)
def create_user(data: UsuarioIn, db: Session = Depends(get_db), admin=Depends(require_permission("usuarios:escribir"))):
    if not db.get(Role, data.role_id): raise HTTPException(404, "Rol no encontrado")
    u = Usuario(username=data.username, nombre=data.nombre, role_id=data.role_id,
                password_hash=hash_password(data.password)); db.add(u)
    try:
        db.flush()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "El usuario ya existe")
    audit(db, admin.id, "CREAR", "usuarios", u.id); db.commit()
    return u

@router.post("/{uid}/deactivate", response_model=UsuarioOut)
def deactivate(uid: int, db: Session = Depends(get_db), admin=Depends(require_permission("usuarios:escribir"))):
    u = db.get(Usuario, uid)
    if not u: raise HTTPException(404, "Usuario no encontrado")
    if u.id == admin.id: raise HTTPException(409, "No puede desactivarse a sí mismo")
    u.activo = False
    audit(db, admin.id, "DESACTIVAR", "usuarios", uid); db.commit()
    return u
