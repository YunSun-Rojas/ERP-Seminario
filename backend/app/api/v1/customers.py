from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Cliente
from backend.app.schemas.schemas import ClienteIn, ClienteOut
from backend.app.security.auth import require_permission
from backend.app.services.audit import audit

router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("", response_model=list[ClienteOut])
def list_customers(q: str | None = None, skip: int = 0, limit: int = Query(50, le=200),
                   db: Session = Depends(get_db), _=Depends(require_permission("clientes:leer"))):
    stmt = select(Cliente).where(Cliente.activo.is_(True))
    if q:
        stmt = stmt.where(Cliente.nombre.ilike(f"%{q}%") | Cliente.documento.ilike(f"%{q}%"))
    return db.scalars(stmt.order_by(Cliente.nombre).offset(skip).limit(limit)).all()

@router.post("", response_model=ClienteOut, status_code=201)
def create_customer(data: ClienteIn, db: Session = Depends(get_db), user=Depends(require_permission("clientes:escribir"))):
    c = Cliente(**data.model_dump()); db.add(c)
    try:
        db.flush()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "Ya existe un cliente con ese documento")
    audit(db, user.id, "CREAR", "clientes", c.id); db.commit()
    return c

@router.put("/{cid}", response_model=ClienteOut)
def update_customer(cid: int, data: ClienteIn, db: Session = Depends(get_db), user=Depends(require_permission("clientes:escribir"))):
    c = db.get(Cliente, cid)
    if not c: raise HTTPException(404, "Cliente no encontrado")
    for k, v in data.model_dump().items(): setattr(c, k, v)
    audit(db, user.id, "EDITAR", "clientes", cid); db.commit()
    return c

@router.delete("/{cid}", status_code=204)
def delete_customer(cid: int, db: Session = Depends(get_db), user=Depends(require_permission("clientes:escribir"))):
    c = db.get(Cliente, cid)
    if not c: raise HTTPException(404, "Cliente no encontrado")
    c.activo = False  # baja lógica: conserva historial de ventas
    audit(db, user.id, "DESACTIVAR", "clientes", cid); db.commit()
