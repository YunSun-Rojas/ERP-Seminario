from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Proveedor
from backend.app.schemas.schemas import ProveedorIn, ProveedorOut
from backend.app.security.auth import require_permission
from backend.app.services.audit import audit

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

@router.get("", response_model=list[ProveedorOut])
def list_suppliers(skip: int = 0, limit: int = Query(50, le=200), db: Session = Depends(get_db),
                   _=Depends(require_permission("proveedores:leer"))):
    return db.scalars(select(Proveedor).where(Proveedor.activo.is_(True)).order_by(Proveedor.nombre).offset(skip).limit(limit)).all()

@router.post("", response_model=ProveedorOut, status_code=201)
def create_supplier(data: ProveedorIn, db: Session = Depends(get_db), user=Depends(require_permission("proveedores:escribir"))):
    p = Proveedor(**data.model_dump()); db.add(p)
    try:
        db.flush()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "Ya existe un proveedor con ese documento")
    audit(db, user.id, "CREAR", "proveedores", p.id); db.commit()
    return p

@router.put("/{pid}", response_model=ProveedorOut)
def update_supplier(pid: int, data: ProveedorIn, db: Session = Depends(get_db), user=Depends(require_permission("proveedores:escribir"))):
    p = db.get(Proveedor, pid)
    if not p: raise HTTPException(404, "Proveedor no encontrado")
    for k, v in data.model_dump().items(): setattr(p, k, v)
    audit(db, user.id, "EDITAR", "proveedores", pid); db.commit()
    return p

@router.delete("/{pid}", status_code=204)
def delete_supplier(pid: int, db: Session = Depends(get_db), user=Depends(require_permission("proveedores:escribir"))):
    p = db.get(Proveedor, pid)
    if not p: raise HTTPException(404, "Proveedor no encontrado")
    p.activo = False
    audit(db, user.id, "DESACTIVAR", "proveedores", pid); db.commit()
