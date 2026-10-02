from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Compra
from backend.app.schemas.schemas import CompraIn, CompraOut
from backend.app.security.auth import require_permission
from backend.app.services import purchases_service

router = APIRouter(prefix="/purchases", tags=["purchases"])

@router.post("", response_model=CompraOut, status_code=201)
def create(data: CompraIn, db: Session = Depends(get_db), user=Depends(require_permission("compras:escribir"))):
    try:
        c = purchases_service.create_purchase(db, data, user); db.commit()
    except Exception:
        db.rollback(); raise
    return c

@router.get("", response_model=list[CompraOut])
def list_purchases(skip: int = 0, limit: int = Query(50, le=200), db: Session = Depends(get_db),
                   _=Depends(require_permission("compras:leer"))):
    return db.scalars(select(Compra).order_by(Compra.id.desc()).offset(skip).limit(limit)).all()

@router.get("/{cid}", response_model=CompraOut)
def get_purchase(cid: int, db: Session = Depends(get_db), _=Depends(require_permission("compras:leer"))):
    c = db.get(Compra, cid)
    if not c: raise HTTPException(404, "Compra no encontrada")
    return c
