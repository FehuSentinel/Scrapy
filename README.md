# 🗄️ Data Warehouse Kimball - Sistema de Análisis de Ventas E-commerce

Un sistema completo de Data Warehouse basado en el modelo Kimball para análisis de ventas de comercio electrónico, con scraping integrado y generación automática de datos.

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Modelo de Datos](#-modelo-de-datos)
- [Consultas de Ejemplo](#-consultas-de-ejemplo)
- [Troubleshooting](#-troubleshooting)
- [Contribución](#-contribución)
- [Licencia](#-licencia)

## 🎯 Descripción

Este proyecto implementa un Data Warehouse completo siguiendo la metodología Kimball, diseñado para análisis de ventas de comercio electrónico. Incluye:

- **Scraping automático** de productos reales de tiendas online
- **Generación de datos** de usuarios aleatorios con perfiles realistas
- **Simulación de ventas** basada en patrones demográficos
- **Carga automática** de datos a PostgreSQL
- **Interfaz interactiva** para gestión completa del sistema

## ✨ Características

- 🕷️ **Scraping Integrado**: Extrae productos reales de tiendas online
- 👥 **Usuarios Realistas**: Genera perfiles con edad, sexo y comportamiento
- 🛍️ **Productos Reales**: Información actualizada de productos con precios
- 🏪 **Tiendas Múltiples**: Soporte para múltiples tiendas con direcciones reales
- 💰 **Ventas Simuladas**: Transacciones realistas basadas en patrones demográficos
- 📊 **Análisis Completo**: Consultas multidimensionales típicas de Kimball
- 🔄 **Proceso Automatizado**: Generación y carga de datos en un solo paso
- 📈 **Reportes**: Visualización de datos y estadísticas

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Scraping  │    │  Data Generator │    │   PostgreSQL    │
│   (Productos)   │    │   (Usuarios)    │    │   DataWarehouse │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Scraper        │
                    │  Integrado      │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Cargador CSV   │
                    └─────────────────┘
```

## 📋 Requisitos

### Software Requerido
- **Python 3.8+**
- **PostgreSQL 12+**
- **Git** (para clonar el repositorio)

### Sistema Operativo
- Windows 10/11
- macOS 10.15+
- Ubuntu 18.04+ / Debian 10+

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/FehuSentinel/Scrapy.git
cd Scrapy
```

### 2. Crear Entorno Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar PostgreSQL

1. **Instalar PostgreSQL** desde [postgresql.org](https://www.postgresql.org/download/)
2. **Crear una base de datos**:
   ```sql
   CREATE DATABASE alquimia;
   CREATE USER tu_usuario WITH PASSWORD 'tu_contraseña';
   GRANT ALL PRIVILEGES ON DATABASE alquimia TO tu_usuario;
   ```

## ⚙️ Configuración

### 1. Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
# Configuración de Base de Datos
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alquimia

# Configuración de Scraping (opcional)
SCRAPING_DELAY=1
MAX_RETRIES=3
```

### 2. Verificar Conexión

Ejecutar el script de verificación:

```bash
python verificar_tabla.py
```

## 🎮 Uso

### Ejecutar el Sistema Principal

```bash
python main.py
```

### Menú Principal

```
==================================================
    🗄️  GESTOR DE DATOS POSTGRESQL
==================================================
1. 📊 Generar nuevos datos (RandomUser API)
2. 🕷️  Web scraping de productos
3. 🚀 Scraper Integrado (Datos Completos)
4. 📁 Cargar archivo CSV a la base de datos
5. 📂 Ver archivos disponibles
6. 🗄️ Ver tablas de la base de datos
0. 🚪 Salir
==================================================
```

### Opciones Disponibles

#### 1. Generar Datos de Usuarios
- Crea perfiles de usuarios aleatorios con edad y sexo
- Utiliza la API RandomUser.me
- Genera archivo CSV con datos demográficos

#### 2. Scraping de Productos
- Extrae productos reales de tiendas online
- Obtiene precios, marcas y URLs actualizadas
- Genera archivo CSV con información de productos

#### 3. Scraper Integrado (Recomendado)
- **Opción más completa**: Genera todos los datos automáticamente
- Usuarios con perfiles realistas
- Productos extraídos de tiendas reales
- Ventas simuladas basadas en patrones demográficos
- Promociones y fechas automáticas
- Un solo archivo con toda la información

#### 4. Cargar CSV
- Sube archivos CSV a la base de datos
- Manejo automático de duplicados
- Validación de integridad referencial

#### 5. Ver Archivos
- Lista archivos CSV disponibles
- Muestra tamaño y ubicación

#### 6. Ver Tablas
- Explorador interactivo de la base de datos
- Consultas predefinidas
- Visualización de datos

## 📁 Estructura del Proyecto

```
Scrapy/
├── 📄 main.py                 # Menú principal del sistema
├── 📄 models.py               # Modelos SQLAlchemy
├── 📄 scrapy_integrado.py     # Scraper completo (recomendado)
├── 📄 scrapyuser.py           # Generador de usuarios
├── 📄 scrapyProductos.py      # Scraper de productos
├── 📄 cargar_csv.py           # Cargador de archivos CSV
├── 📄 ver_tablas_db.py        # Visor de tablas
├── 📄 verificar_tabla.py      # Verificador de conexión
├── 📄 requirements.txt        # Dependencias Python
├── 📄 .env                    # Variables de entorno (NO subir)
├── 📄 .gitignore             # Archivos ignorados por Git
├── 📂 archivos/              # Archivos CSV generados
├── 📂 venv/                  # Entorno virtual
└── 📄 README.md              # Este archivo
```

## 🗃️ Modelo de Datos

### Tablas del Data Warehouse

#### Dimensiones
- **usuarios**: Perfiles de clientes con edad y sexo
- **productos**: Catálogo de productos con precios
- **tienda**: Información de tiendas online
- **promocion**: Descuentos y ofertas
- **tiempo**: Dimensiones temporales para análisis

#### Hechos
- **ventas**: Transacciones con métricas completas

### Relaciones
```
usuarios (1) ←→ (N) ventas
productos (1) ←→ (N) ventas
tienda (1) ←→ (N) ventas
promocion (1) ←→ (N) ventas
tiempo (1) ←→ (N) ventas
```

## 📊 Consultas de Ejemplo

### Ventas por Rango Etario
```sql
SELECT 
    u.edad,
    COUNT(*) as total_ventas,
    SUM(v.total_neto) as ingresos_totales
FROM ventas v
JOIN usuarios u ON v.id_usuario = u.id_usuario
GROUP BY u.edad
ORDER BY ingresos_totales DESC;
```

### Productos Más Vendidos
```sql
SELECT 
    p.nombre,
    p.marca,
    COUNT(*) as veces_vendido,
    SUM(v.cantidad_vendida) as unidades_vendidas
FROM ventas v
JOIN productos p ON v.id_producto = p.id_producto
GROUP BY p.id_producto, p.nombre, p.marca
ORDER BY unidades_vendidas DESC;
```

### Análisis Temporal
```sql
SELECT 
    t.año,
    t.mes,
    COUNT(*) as ventas_mes,
    SUM(v.total_neto) as ingresos_mes
FROM ventas v
JOIN tiempo t ON v.id_tiempo = t.id_tiempo
GROUP BY t.año, t.mes
ORDER BY t.año, t.mes;
```

## 🔧 Troubleshooting

### Error de Conexión a PostgreSQL
```
❌ Error: connection to server at "localhost" failed
```
**Solución:**
1. Verificar que PostgreSQL esté ejecutándose
2. Comprobar credenciales en `.env`
3. Verificar que la base de datos `alquimia` exista

### Error de Dependencias
```
❌ ModuleNotFoundError: No module named 'psycopg2'
```
**Solución:**
```bash
pip install -r requirements.txt
```

### Error de Permisos
```
❌ Permission denied: .env
```
**Solución:**
1. Verificar permisos del archivo `.env`
2. Crear el archivo si no existe

### Error de Llaves Foráneas
```
❌ Foreign key violation
```
**Solución:**
1. Usar el **Scraper Integrado** (opción 3)
2. Los datos se cargan en el orden correcto automáticamente

### Error de Scraping
```
❌ Connection timeout
```
**Solución:**
1. Verificar conexión a internet
2. Aumentar `SCRAPING_DELAY` en `.env`
3. Reintentar la operación

## 📈 Casos de Uso

### Análisis de Ventas
- Identificar productos más populares por demografía
- Analizar patrones de compra por edad y sexo
- Evaluar efectividad de promociones

### Business Intelligence
- Reportes de ventas por período
- Análisis de tendencias temporales
- Segmentación de clientes

### Optimización de Inventario
- Productos con mayor rotación
- Predicción de demanda por temporada
- Análisis de rentabilidad por producto

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas:
- Crear un issue en el repositorio
- Revisar la documentación en `Informe_Completo.docx`
- Consultar las consultas de ejemplo en este README

---

**¡Disfruta analizando tus datos de e-commerce! 🚀**
