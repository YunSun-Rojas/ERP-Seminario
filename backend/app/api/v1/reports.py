from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Compra, Inventario, Pago, Producto, Venta
from backend.app.security.auth import require_permission

router = APIRouter(prefix="/reports", tags=["reports"])

def _sum(db, stmt) -> Decimal:
    return Decimal(str(db.scalar(stmt) or 0))

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _=Depends(require_permission("reportes:leer"))):
    now = datetime.now(timezone.utc)
    hoy = now.replace(hour=0, minute=0, second=0, microsecond=0)
    mes = hoy.replace(day=1)
    vs = lambda since: _sum(db, select(func.sum(Venta.total)).where(Venta.estado == "EMITIDA", Venta.fecha >= since))
    ventas_total = _sum(db, select(func.sum(Venta.total)).where(Venta.estado == "EMITIDA"))
    cobrado = _sum(db, select(func.sum(Pago.monto)).join(Venta, Venta.id == Pago.venta_id).where(Venta.estado == "EMITIDA"))
    compras_total = _sum(db, select(func.sum(Compra.total)).where(Compra.estado != "ANULADA"))
    pagado = _sum(db, select(func.sum(Pago.monto)).join(Compra, Compra.id == Pago.compra_id).where(Compra.estado != "ANULADA"))
    bajo = db.scalar(select(func.count()).select_from(Inventario).join(Producto, Producto.id == Inventario.producto_id)
                     .where(Inventario.cantidad <= Producto.stock_minimo)) or 0
    return {"ventas_hoy": vs(hoy), "ventas_mes": vs(mes),
            "compras_mes": _sum(db, select(func.sum(Compra.total)).where(Compra.estado != "ANULADA", Compra.fecha >= mes)),
            "cuentas_por_cobrar": ventas_total - cobrado, "cuentas_por_pagar": compras_total - pagado,
            "productos_stock_critico": bajo}
