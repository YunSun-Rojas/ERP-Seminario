from fastapi import APIRouter
from backend.app.api.v1 import users
from backend.app.api.v1 import auth, customers, documents, inventory, payments, products, purchases, reports, sales, suppliers

api_router = APIRouter(prefix="/api/v1")
for m in (auth, users, customers, suppliers, products, inventory, sales, purchases, payments, documents, reports):
    api_router.include_router(m.router)
