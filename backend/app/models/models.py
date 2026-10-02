from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

def utcnow():
    return datetime.now(timezone.utc)

roles_permisos = Table(
    "roles_permisos", Base.metadata,
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
    Column("permiso_id", ForeignKey("permisos.id"), primary_key=True),
)

class Permiso(Base):
    __tablename__ = "permisos"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True)  # ej. ventas:escribir

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True)
    permisos: Mapped[list[Permiso]] = relationship(secondary=roles_permisos, lazy="selectin")

class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(100))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[Role] = relationship(lazy="joined")

class Cliente(Base):
    __tablename__ = "clientes"
    id: Mapped[int] = mapped_column(primary_key=True)
    documento: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(150), index=True)
    email: Mapped[str | None] = mapped_column(String(120))
    telefono: Mapped[str | None] = mapped_column(String(30))
    direccion: Mapped[str | None] = mapped_column(String(200))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

class Proveedor(Base):
    __tablename__ = "proveedores"
    id: Mapped[int] = mapped_column(primary_key=True)
    documento: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(150), index=True)
    email: Mapped[str | None] = mapped_column(String(120))
    telefono: Mapped[str | None] = mapped_column(String(30))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

class Categoria(Base):
    __tablename__ = "categorias"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)

class Producto(Base):
    __tablename__ = "productos"
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(150), index=True)
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id"))
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    costo: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    stock_minimo: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

class Almacen(Base):
    __tablename__ = "almacenes"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)

class Inventario(Base):
    __tablename__ = "inventarios"
    __table_args__ = (UniqueConstraint("producto_id", "almacen_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), index=True)
    almacen_id: Mapped[int] = mapped_column(ForeignKey("almacenes.id"))
    cantidad: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)

class MovimientoInventario(Base):  # kardex
    __tablename__ = "movimientos_inventario"
    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), index=True)
    almacen_id: Mapped[int] = mapped_column(ForeignKey("almacenes.id"))
    tipo: Mapped[str] = mapped_column(String(10))  # ENTRADA | SALIDA
    cantidad: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # con signo
    saldo: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    referencia: Mapped[str | None] = mapped_column(String(60))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Venta(Base):
    __tablename__ = "ventas"
    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(40), unique=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    igv: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    estado: Mapped[str] = mapped_column(String(10), default="EMITIDA")  # EMITIDA | ANULADA
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    detalles: Mapped[list["DetalleVenta"]] = relationship(back_populates="venta", lazy="selectin")

class DetalleVenta(Base):
    __tablename__ = "detalle_ventas"
    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    almacen_id: Mapped[int] = mapped_column(ForeignKey("almacenes.id"))
    cantidad: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    venta: Mapped[Venta] = relationship(back_populates="detalles")

class Auditoria(Base):
    __tablename__ = "auditoria"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    accion: Mapped[str] = mapped_column(String(40))
    modulo: Mapped[str] = mapped_column(String(40))
    registro: Mapped[str | None] = mapped_column(String(60))
    resultado: Mapped[str] = mapped_column(String(10), default="OK")
    detalle: Mapped[str | None] = mapped_column(Text)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Compra(Base):
    __tablename__ = "compras"
    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(40), unique=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    igv: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    estado: Mapped[str] = mapped_column(String(10), default="RECIBIDA")
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    detalles: Mapped[list["DetalleCompra"]] = relationship(back_populates="compra", lazy="selectin")

class DetalleCompra(Base):
    __tablename__ = "detalle_compras"
    id: Mapped[int] = mapped_column(primary_key=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compras.id"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    almacen_id: Mapped[int] = mapped_column(ForeignKey("almacenes.id"))
    cantidad: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    costo_unitario: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    compra: Mapped[Compra] = relationship(back_populates="detalles")

class Pago(Base):
    __tablename__ = "pagos"
    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(6))  # COBRO (CxC) | PAGO (CxP)
    venta_id: Mapped[int | None] = mapped_column(ForeignKey("ventas.id"), index=True)
    compra_id: Mapped[int | None] = mapped_column(ForeignKey("compras.id"), index=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    metodo: Mapped[str] = mapped_column(String(20))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Documento(Base):
    __tablename__ = "documentos"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    s3_key: Mapped[str] = mapped_column(String(400), unique=True)
    content_type: Mapped[str] = mapped_column(String(100))
    tamano: Mapped[int]
    entidad: Mapped[str] = mapped_column(String(30), index=True)  # venta | compra | cliente ...
    entidad_id: Mapped[int] = mapped_column(index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
