from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.app.api.v1.router import api_router
from backend.app.core.database import Base, engine
import backend.app.models  # noqa: F401  (registra tablas)

@asynccontextmanager
async def lifespan(_):
    Base.metadata.create_all(engine)  # en producción: migraciones con Alembic
    yield

backend.app = FastAPI(title="ERP EnterpriseCloud", version="1.0.0", lifespan=lifespan)
backend.app.include_router(api_router)

@backend.app.get("/health", tags=["ops"])
def health():
    return {"status": "ok"}

