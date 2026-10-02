from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ClienteIn(BaseModel):
    documento: str = Field(min_length=8, max_length=20)
    nombre: str = Field(min_length=2, max_length=150)
    email: str | None = None
    telefono: str | None = None
    direccion: str | None = None
class ClienteOut(ClienteIn, ORM):
    id: int
    activo: bool

class ProductoIn(BaseModel):
    sku: str = Field(min_length=1, max_length=40)
    nombre: str = Field(min_length=2, max_length=150)
    categoria_id: int | None = None
    precio_venta: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    costo: Decimal = Field(default=Decimal(0), ge=0, max_digits=14, decimal_places=2)
    stock_minimo: Decimal = Field(default=Decimal(0), ge=0)
class ProductoOut(ProductoIn, ORM):
    id: int
    activo: bool

class MovimientoIn(BaseModel):
    producto_id: int
    almacen_id: int
    tipo: str = Field(pattern="^(ENTRADA|SALIDA)$")
    cantidad: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    referencia: str | None = None
class StockOut(ORM):
    producto_id: int
    almacen_id: int
    cantidad: Decimal

class ItemIn(BaseModel):
    producto_id: int
    almacen_id: int
    cantidad: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    precio_unitario: Decimal | None = Field(default=None, ge=0)  # None = precio del producto
class VentaIn(BaseModel):
    cliente_id: int
    items: list[ItemIn] = Field(min_length=1)
class DetalleOut(ORM):
    producto_id: int
    almacen_id: int
    cantidad: Decimal
    precio_unitario: Decimal
    subtotal: Decimal
class VentaOut(ORM):
    id: int
    numero: str
    cliente_id: int
    subtotal: Decimal
    igv: Decimal
    total: Decimal
    estado: str
    fecha: datetime
    detalles: list[DetalleOut]

class ProveedorIn(BaseModel):
    documento: str = Field(min_length=8, max_length=20)
    nombre: str = Field(min_length=2, max_length=150)
    email: str | None = None
    telefono: str | None = None
class ProveedorOut(ProveedorIn, ORM):
    id: int
    activo: bool

class CompraItemIn(BaseModel):
    producto_id: int
    almacen_id: int
    cantidad: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    costo_unitario: Decimal = Field(ge=0)
class CompraIn(BaseModel):
    proveedor_id: int
    items: list[CompraItemIn] = Field(min_length=1)
class DetalleCompraOut(ORM):
    producto_id: int
    almacen_id: int
    cantidad: Decimal
    costo_unitario: Decimal
    subtotal: Decimal
class CompraOut(ORM):
    id: int
    numero: str
    proveedor_id: int
    subtotal: Decimal
    igv: Decimal
    total: Decimal
    estado: str
    fecha: datetime
    detalles: list[DetalleCompraOut]

class PagoIn(BaseModel):
    venta_id: int | None = None
    compra_id: int | None = None
    monto: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    metodo: str = Field(pattern="^(EFECTIVO|TRANSFERENCIA|TARJETA|YAPE|PLIN)$")
class PagoOut(PagoIn, ORM):
    id: int
    tipo: str

class UsuarioIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    nombre: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=72)
    role_id: int
class UsuarioOut(ORM):
    id: int
    username: str
    nombre: str
    role_id: int
    activo: bool
