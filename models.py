import os
from sqlalchemy import Column, Integer, String, Text, create_engine, ForeignKey, Numeric, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from dotenv import load_dotenv

# Cargar variables de entorno (intenta .env primero, luego config.env)
load_dotenv('.env')  # Intenta cargar .env
load_dotenv('config.env', override=True)  # Sobrescribe con config.env si existe

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    apellido = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    edad = Column(String(255), nullable=False)
    sexo = Column(String(255), nullable=False)
    
    # Relaciones
    ventas = relationship("Venta", back_populates="usuario")

class Direccion(Base):
    __tablename__ = 'direccion'
    
    id_direccion = Column(Integer, primary_key=True, autoincrement=True)
    calle = Column(String(100), nullable=False)
    numero = Column(String(10), nullable=False)
    comuna = Column(String(50), nullable=False)
    ciudad = Column(String(50), nullable=False)
    region = Column(String(50), nullable=False)
    
    # Relaciones
    tiendas = relationship("Tienda", back_populates="direccion_rel")

class Tienda(Base):
    __tablename__ = 'tienda'
    
    id_tienda = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)
    direccion = Column(String(255), nullable=True)
    url = Column(String(255), nullable=True)
    id_direccion = Column(Integer, ForeignKey('direccion.id_direccion'), nullable=True)
    
    # Relaciones
    direccion_rel = relationship("Direccion", back_populates="tiendas")
    productos = relationship("Producto", back_populates="tienda")
    ventas = relationship("Venta", back_populates="tienda")

class Producto(Base):
    __tablename__ = 'productos'
    
    id_producto = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    marca = Column(String(100), nullable=True)
    precio = Column(Numeric(10, 2), nullable=True)
    url_producto = Column(Text, nullable=True)
    promocion = Column(Integer, ForeignKey('promocion.id_promocion'), nullable=True)
    preciofinal = Column(Numeric(10, 2), nullable=True)
    id_tienda = Column(Integer, ForeignKey('tienda.id_tienda'), nullable=True)
    
    # Relaciones
    tienda = relationship("Tienda", back_populates="productos")
    ventas = relationship("Venta", back_populates="producto")
    promocion_rel = relationship("Promocion")

class Promocion(Base):
    __tablename__ = 'promocion'
    
    id_promocion = Column(Integer, primary_key=True, autoincrement=True)
    tipo_promocion = Column(String(50), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    
    # Relaciones
    productos = relationship("Producto", back_populates="promocion_rel")
    ventas = relationship("Venta", back_populates="promocion")

class Tiempo(Base):
    __tablename__ = 'tiempo'
    
    id_tiempo = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    dia = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    año = Column(Integer, nullable=False)
    trimestre = Column(Integer, nullable=False)
    festivo = Column(Boolean, nullable=False, default=False)
    
    # Relaciones
    ventas = relationship("Venta", back_populates="tiempo")

class Venta(Base):
    __tablename__ = 'ventas'
    
    id_venta = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    id_producto = Column(Integer, ForeignKey('productos.id_producto'), nullable=False)
    id_tienda = Column(Integer, ForeignKey('tienda.id_tienda'), nullable=False)
    id_tiempo = Column(Integer, ForeignKey('tiempo.id_tiempo'), nullable=False)
    id_promocion = Column(Integer, ForeignKey('promocion.id_promocion'), nullable=True)
    cantidad_vendida = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    descuento_unitario = Column(Numeric(10, 2), nullable=False)
    precio_final_unitario = Column(Numeric(10, 2), nullable=False)
    total_bruto = Column(Numeric(12, 2), nullable=False)
    total_descuento = Column(Numeric(12, 2), nullable=False)
    total_neto = Column(Numeric(12, 2), nullable=False)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="ventas")
    producto = relationship("Producto", back_populates="ventas")
    tienda = relationship("Tienda", back_populates="ventas")
    tiempo = relationship("Tiempo", back_populates="ventas")
    promocion = relationship("Promocion", back_populates="ventas")

# Crear la conexión a PostgreSQL usando variables de entorno
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'tu_contraseña')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'alquimia')

DATABASE_URL = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(DATABASE_URL)

# Crear las tablas (si no existen, no hace nada)
Base.metadata.create_all(engine)
