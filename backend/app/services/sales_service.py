from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from sqlalchemy import select
from backend.app.models import Pago, Almacen, Cliente, DetalleVenta, Producto, Usuario, Venta
from backend.app.schemas.schemas import VentaIn
from backend.app.services.audit import audit
from backend.app.services.inventory_service import apply_movement

def money(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), ROUND_HALF_UP)

def create_sale(db: Session, data: VentaIn, user: Usuario) -> Venta:
    cliente = db.get(Cliente, data.cliente_id)
    if not cliente or not cliente.activo:
        raise HTTPException(404, "Cliente no encontrado")
    venta = Venta(numero=f"TMP-{uuid4().hex}", cliente_id=cliente.id, usuario_id=user.id,
                  subtotal=0, igv=0, total=0)
    db.add(venta); db.flush()
    subtotal = Decimal(0)
    for it in sorted(data.items, key=lambda i: (i.producto_id, i.almacen_id)):  # orden fijo evita deadlocks
        prod = db.get(Producto, it.producto_id)
        if not prod or not prod.activo:
            raise HTTPException(404, f"Producto {it.producto_id} no encontrado")
        if not db.get(Almacen, it.almacen_id):
            raise HTTPException(404, f"Almacén {it.almacen_id} no encontrado")
        precio = it.precio_unitario if it.precio_unitario is not None else prod.precio_venta
        linea = money(it.cantidad * precio)
        subtotal += linea
        db.add(DetalleVenta(venta_id=venta.id, producto_id=prod.id, almacen_id=it.almacen_id,
                            cantidad=it.cantidad, precio_unitario=precio, subtotal=linea))
        apply_movement(db, producto_id=prod.id, almacen_id=it.almacen_id, delta=-it.cantidad,
                       tipo="SALIDA", usuario_id=user.id, referencia=f"VENTA-{venta.id}")
    venta.subtotal = money(subtotal)
    venta.igv = money(subtotal * settings.IGV_RATE)
    venta.total = venta.subtotal + venta.igv
    venta.numero = f"V-{venta.id:08d}"
    audit(db, user.id, "CREAR", "ventas", venta.numero)
    return venta

def cancel_sale(db: Session, venta_id: int, user: Usuario) -> Venta:
    venta = db.get(Venta, venta_id)
    if not venta:
        raise HTTPException(404, "Venta no encontrada")
    if venta.estado == "ANULADA":
        raise HTTPException(409, "La venta ya está anulada")
    if db.scalar(select(Pago.id).where(Pago.venta_id == venta.id)):
        raise HTTPException(409, "No se puede anular una venta con cobros registrados")
    for d in venta.detalles:
        apply_movement(db, producto_id=d.producto_id, almacen_id=d.almacen_id, delta=d.cantidad,
                       tipo="ENTRADA", usuario_id=user.id, referencia=f"ANULA-{venta.numero}")
    venta.estado = "ANULADA"
    audit(db, user.id, "ANULAR", "ventas", venta.numero)
    return venta
