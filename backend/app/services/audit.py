from sqlalchemy.orm import Session
from backend.app.models import Auditoria

def audit(db: Session, user_id, accion, modulo, registro=None, resultado="OK", detalle=None):
    db.add(Auditoria(usuario_id=user_id, accion=accion, modulo=modulo,
                     registro=str(registro) if registro is not None else None,
                     resultado=resultado, detalle=detalle))
