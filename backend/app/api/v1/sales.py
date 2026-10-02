from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Venta
from backend.app.schemas.schemas import VentaIn, VentaOut
from backend.app.security.auth import require_permission
from backend.app.services import sales_service

router = APIRouter(prefix="/sales", tags=["sales"])

@router.post("", response_model=VentaOut, status_code=201)
def create(data: VentaIn, db: Session = Depends(get_db), user=Depends(require_permission("ventas:escribir"))):
    try:
        venta = sales_service.create_sale(db, data, user); db.commit()
    except Exception:
        db.rollback(); raise  # atómico: o se guarda todo o nada
    return venta

@router.get("", response_model=list[VentaOut])
def list_sales(skip: int = 0, limit: int = Query(50, le=200), db: Session = Depends(get_db),
               _=Depends(require_permission("ventas:leer"))):
    return db.scalars(select(Venta).order_by(Venta.id.desc()).offset(skip).limit(limit)).all()

@router.get("/{vid}", response_model=VentaOut)
def get_sale(vid: int, db: Session = Depends(get_db), _=Depends(require_permission("ventas:leer"))):
    v = db.get(Venta, vid)
    if not v: raise HTTPException(404, "Venta no encontrada")
    return v

@router.post("/{vid}/cancel", response_model=VentaOut)
def cancel(vid: int, db: Session = Depends(get_db), user=Depends(require_permission("ventas:escribir"))):
    try:
        v = sales_service.cancel_sale(db, vid, user); db.commit()
    except Exception:
        db.rollback(); raise
    return v
