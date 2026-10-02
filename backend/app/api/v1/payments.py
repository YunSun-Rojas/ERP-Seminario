from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Compra, Pago, Venta
from backend.app.schemas.schemas import PagoIn, PagoOut
from backend.app.security.auth import require_permission
from backend.app.services.audit import audit

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("", response_model=PagoOut, status_code=201)
def register(data: PagoIn, db: Session = Depends(get_db), user=Depends(require_permission("pagos:escribir"))):
    if bool(data.venta_id) == bool(data.compra_id):
        raise HTTPException(422, "Indique venta_id (cobro) o compra_id (pago), solo uno")
    if data.venta_id:
        doc, tipo, col = db.get(Venta, data.venta_id), "COBRO", Pago.venta_id
        ref = data.venta_id
    else:
        doc, tipo, col = db.get(Compra, data.compra_id), "PAGO", Pago.compra_id
        ref = data.compra_id
    if not doc: raise HTTPException(404, "Documento no encontrado")
    if doc.estado == "ANULADA": raise HTTPException(409, "Documento anulado")
    pagado = Decimal(str(db.scalar(select(func.coalesce(func.sum(Pago.monto), 0)).where(col == ref).with_for_update()) or 0))
    saldo = doc.total - pagado
    if data.monto > saldo:
        raise HTTPException(409, f"El monto excede el saldo pendiente ({saldo})")
    p = Pago(tipo=tipo, venta_id=data.venta_id, compra_id=data.compra_id, monto=data.monto,
             metodo=data.metodo, usuario_id=user.id)
    db.add(p); db.flush()
    audit(db, user.id, tipo, "pagos", p.id); db.commit()
    return p
