import re
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models import Documento
from backend.app.security.auth import require_permission
from backend.app.services.audit import audit

router = APIRouter(prefix="/documents", tags=["documents"])
MAX_BYTES = 10 * 1024 * 1024
ALLOWED = {"application/pdf", "image/png", "image/jpeg", "text/plain",
           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
           "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}

def _s3():
    if not settings.S3_BUCKET:
        raise HTTPException(503, "S3 no configurado (defina S3_BUCKET)")
    import boto3  # credenciales vía rol IAM de la EC2 (sin claves en código)
    return boto3.client("s3", region_name=settings.AWS_REGION)

@router.post("", status_code=201)
def upload(entidad: str, entidad_id: int, file: UploadFile, db: Session = Depends(get_db),
           user=Depends(require_permission("documentos:escribir"))):
    if file.content_type not in ALLOWED: raise HTTPException(415, "Tipo de archivo no permitido")
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES: raise HTTPException(413, "Archivo mayor a 10 MB")
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename or "archivo")
    key = f"{entidad}/{entidad_id}/{uuid4().hex}_{safe}"
    _s3().put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType=file.content_type,
                     ServerSideEncryption="AES256")
    d = Documento(nombre=safe, s3_key=key, content_type=file.content_type, tamano=len(data),
                  entidad=entidad, entidad_id=entidad_id, usuario_id=user.id)
    db.add(d); db.flush(); audit(db, user.id, "SUBIR", "documentos", d.id); db.commit()
    return {"id": d.id, "nombre": d.nombre, "tamano": d.tamano}

@router.get("")
def list_docs(entidad: str, entidad_id: int, db: Session = Depends(get_db), _=Depends(require_permission("documentos:leer"))):
    rows = db.scalars(select(Documento).where(Documento.entidad == entidad, Documento.entidad_id == entidad_id)).all()
    return [{"id": d.id, "nombre": d.nombre, "tamano": d.tamano, "fecha": d.fecha} for d in rows]

@router.get("/{did}/url")
def download_url(did: int, db: Session = Depends(get_db), user=Depends(require_permission("documentos:leer"))):
    d = db.get(Documento, did)
    if not d: raise HTTPException(404, "Documento no encontrado")
    url = _s3().generate_presigned_url("get_object", Params={"Bucket": settings.S3_BUCKET, "Key": d.s3_key}, ExpiresIn=300)
    audit(db, user.id, "DESCARGAR", "documentos", did); db.commit()
    return {"url": url, "expira_en_segundos": 300}
