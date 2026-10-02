"""Datos iniciales: python -m app.seed"""
import os
from backend.app.core.database import Base, SessionLocal, engine
from backend.app.models import Almacen, Permiso, Role, Usuario
from backend.app.security.auth import hash_password

def run():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    if db.query(Role).first():
        print("Ya inicializado"); return
    perms = [Permiso(codigo=f"{m}:{a}") for m in ("clientes", "proveedores", "productos", "inventario", "ventas", "compras", "pagos", "documentos", "reportes", "usuarios") for a in ("leer", "escribir")]
    db.add_all(perms); db.flush()
    admin = Role(nombre="admin")
    vend = Role(nombre="vendedor", permisos=[p for p in perms if p.codigo in
        ("clientes:leer", "clientes:escribir", "productos:leer", "inventario:leer", "ventas:leer", "ventas:escribir", "pagos:leer", "pagos:escribir", "reportes:leer")])
    db.add_all([admin, vend]); db.flush()
    pwd = os.getenv("ADMIN_PASSWORD", "Admin#2026")
    db.add(Usuario(username="admin", nombre="Administrador", password_hash=hash_password(pwd), role_id=admin.id))
    db.add(Almacen(nombre="Principal")); db.commit()
    print(f"Listo. Usuario: admin / Clave: {pwd}")

if __name__ == "__main__":
    run()
