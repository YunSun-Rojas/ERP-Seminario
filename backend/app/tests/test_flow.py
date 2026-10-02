from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app import seed

def test_sale_flow():
    seed.run()
    with TestClient(app) as c:
        t = c.post("/api/v1/auth/login", data={"username": "admin", "password": "Admin#2026"}).json()["access_token"]
        h = {"Authorization": f"Bearer {t}"}
        assert c.get("/api/v1/customers").status_code == 401
        cl = c.post("/api/v1/customers", json={"documento": "20123456789", "nombre": "ACME SAC"}, headers=h).json()
        p = c.post("/api/v1/products", json={"sku": "P1", "nombre": "Mouse", "precio_venta": "100.00"}, headers=h).json()
        c.post("/api/v1/inventory/movements", json={"producto_id": p["id"], "almacen_id": 1, "tipo": "ENTRADA", "cantidad": "10"}, headers=h)
        v = c.post("/api/v1/sales", json={"cliente_id": cl["id"], "items": [{"producto_id": p["id"], "almacen_id": 1, "cantidad": "3"}]}, headers=h).json()
        assert float(v["subtotal"]) == 300 and float(v["igv"]) == 54 and float(v["total"]) == 354
        bad = c.post("/api/v1/sales", json={"cliente_id": cl["id"], "items": [{"producto_id": p["id"], "almacen_id": 1, "cantidad": "8"}]}, headers=h)
        assert bad.status_code == 409
        assert float(c.get("/api/v1/inventory/stock", headers=h).json()[0]["cantidad"]) == 7
        c.post(f"/api/v1/sales/{v['id']}/cancel", headers=h)
        assert float(c.get("/api/v1/inventory/stock", headers=h).json()[0]["cantidad"]) == 10

def test_purchases_payments_dashboard():
    with TestClient(app) as c:
        t = c.post("/api/v1/auth/login", data={"username": "admin", "password": "Admin#2026"}).json()["access_token"]
        h = {"Authorization": f"Bearer {t}"}
        pr = c.post("/api/v1/suppliers", json={"documento": "20999999999", "nombre": "Proveedor SA"}, headers=h).json()
        p = c.get("/api/v1/products", headers=h).json()[0]
        co = c.post("/api/v1/purchases", json={"proveedor_id": pr["id"], "items": [{"producto_id": p["id"], "almacen_id": 1, "cantidad": "5", "costo_unitario": "40"}]}, headers=h).json()
        assert float(co["total"]) == 236
        assert float(c.get("/api/v1/inventory/stock", headers=h).json()[0]["cantidad"]) == 15
        assert c.post("/api/v1/payments", json={"compra_id": co["id"], "monto": "300", "metodo": "EFECTIVO"}, headers=h).status_code == 409
        assert c.post("/api/v1/payments", json={"compra_id": co["id"], "monto": "100", "metodo": "EFECTIVO"}, headers=h).status_code == 201
        d = c.get("/api/v1/reports/dashboard", headers=h).json()
        assert float(d["cuentas_por_pagar"]) == 136
        assert c.get("/api/v1/users/me", headers=h).json()["username"] == "admin"
