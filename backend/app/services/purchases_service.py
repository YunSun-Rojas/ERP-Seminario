from decimal import Decimal
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models import Almacen, Compra, DetalleCompra, Producto, Proveedor, Usuario
from backend.app.schemas.schemas import CompraIn
from backend.app.services.audit import audit
from backend.app.services.inventory_service import apply_movement
from backend.app.services.sales_service import money

def create_purchase(db: Session, data: CompraIn, user: Usuario) -> Compra:
    prov = db.get(Proveedor, data.proveedor_id)
    if not prov or not prov.activo:
        raise HTTPException(404, "Proveedor no encontrado")
    compra = Compra(numero=f"TMP-{uuid4().hex}", proveedor_id=prov.id, usuario_id=user.id, subtotal=0, igv=0, total=0)
    db.add(compra); db.flush()
    subtotal = Decimal(0)
    for it in sorted(data.items, key=lambda i: (i.producto_id, i.almacen_id)):
        prod = db.get(Producto, it.producto_id)
        if not prod or not prod.activo:
            raise HTTPException(404, f"Producto {it.producto_id} no encontrado")
        if not db.get(Almacen, it.almacen_id):
            raise HTTPException(404, f"Almacén {it.almacen_id} no encontrado")
        linea = money(it.cantidad * it.costo_unitario); subtotal += linea
        db.add(DetalleCompra(compra_id=compra.id, producto_id=prod.id, almacen_id=it.almacen_id,
                             cantidad=it.cantidad, costo_unitario=it.costo_unitario, subtotal=linea))
        apply_movement(db, producto_id=prod.id, almacen_id=it.almacen_id, delta=it.cantidad,
                       tipo="ENTRADA", usuario_id=user.id, referencia=f"COMPRA-{compra.id}")
        prod.costo = it.costo_unitario  # último costo
    compra.subtotal = money(subtotal)
    compra.igv = money(subtotal * settings.IGV_RATE)
    compra.total = compra.subtotal + compra.igv
    compra.numero = f"C-{compra.id:08d}"
    audit(db, user.id, "CREAR", "compras", compra.numero)
    return compra
