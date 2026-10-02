from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models import Inventario, MovimientoInventario

def apply_movement(db: Session, *, producto_id, almacen_id, delta: Decimal, tipo, usuario_id, referencia=None):
    """Única vía para modificar stock: bloquea la fila, valida saldo y registra kardex."""
    inv = db.scalar(select(Inventario).where(Inventario.producto_id == producto_id,
                    Inventario.almacen_id == almacen_id).with_for_update())
    if inv is None:
        inv = Inventario(producto_id=producto_id, almacen_id=almacen_id, cantidad=Decimal(0))
        db.add(inv); db.flush()
    nuevo = inv.cantidad + delta
    if nuevo < 0:
        raise HTTPException(409, f"Stock insuficiente para producto {producto_id} (disponible {inv.cantidad})")
    inv.cantidad = nuevo
    db.add(MovimientoInventario(producto_id=producto_id, almacen_id=almacen_id, tipo=tipo,
                                cantidad=delta, saldo=nuevo, referencia=referencia, usuario_id=usuario_id))
