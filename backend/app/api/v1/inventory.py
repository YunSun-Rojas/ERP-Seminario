from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Almacen, Inventario, Producto
from backend.app.schemas.schemas import MovimientoIn, StockOut
from backend.app.security.auth import require_permission
from backend.app.services.audit import audit
from backend.app.services.inventory_service import apply_movement

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("/stock", response_model=list[StockOut])
def stock(producto_id: int | None = None, db: Session = Depends(get_db), _=Depends(require_permission("inventario:leer"))):
    stmt = select(Inventario)
    if producto_id: stmt = stmt.where(Inventario.producto_id == producto_id)
    return db.scalars(stmt).all()

@router.get("/low-stock")
def low_stock(db: Session = Depends(get_db), _=Depends(require_permission("inventario:leer"))):
    rows = db.execute(select(Producto.id, Producto.sku, Producto.nombre, Producto.stock_minimo, Inventario.cantidad)
                      .join(Inventario, Inventario.producto_id == Producto.id)
                      .where(Inventario.cantidad <= Producto.stock_minimo)).all()
    return [dict(r._mapping) for r in rows]

@router.post("/movements", status_code=201)
def movement(data: MovimientoIn, db: Session = Depends(get_db), user=Depends(require_permission("inventario:escribir"))):
    if not db.get(Producto, data.producto_id) or not db.get(Almacen, data.almacen_id):
        raise HTTPException(404, "Producto o almacén no encontrado")
    delta = data.cantidad if data.tipo == "ENTRADA" else -data.cantidad
    try:
        apply_movement(db, producto_id=data.producto_id, almacen_id=data.almacen_id, delta=delta,
                       tipo=data.tipo, usuario_id=user.id, referencia=data.referencia)
        audit(db, user.id, data.tipo, "inventario", data.producto_id); db.commit()
    except Exception:
        db.rollback(); raise
    return {"ok": True}
