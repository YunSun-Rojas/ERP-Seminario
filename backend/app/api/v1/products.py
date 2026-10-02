from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Producto
from backend.app.schemas.schemas import ProductoIn, ProductoOut
from backend.app.security.auth import require_permission
from backend.app.services.audit import audit

router = APIRouter(prefix="/products", tags=["products"])

@router.get("", response_model=list[ProductoOut])
def list_products(q: str | None = None, skip: int = 0, limit: int = Query(50, le=200),
                  db: Session = Depends(get_db), _=Depends(require_permission("productos:leer"))):
    stmt = select(Producto).where(Producto.activo.is_(True))
    if q:
        stmt = stmt.where(Producto.nombre.ilike(f"%{q}%") | Producto.sku.ilike(f"%{q}%"))
    return db.scalars(stmt.order_by(Producto.nombre).offset(skip).limit(limit)).all()

@router.post("", response_model=ProductoOut, status_code=201)
def create_product(data: ProductoIn, db: Session = Depends(get_db), user=Depends(require_permission("productos:escribir"))):
    p = Producto(**data.model_dump()); db.add(p)
    try:
        db.flush()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "SKU duplicado o categoría inválida")
    audit(db, user.id, "CREAR", "productos", p.id); db.commit()
    return p

@router.put("/{pid}", response_model=ProductoOut)
def update_product(pid: int, data: ProductoIn, db: Session = Depends(get_db), user=Depends(require_permission("productos:escribir"))):
    p = db.get(Producto, pid)
    if not p: raise HTTPException(404, "Producto no encontrado")
    for k, v in data.model_dump().items(): setattr(p, k, v)
    audit(db, user.id, "EDITAR", "productos", pid); db.commit()
    return p
