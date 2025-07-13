# SCRAPER INTEGRADO - GENERADOR DE DATOS COMPLETOS
import requests
import pandas as pd
import os
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
import time
import sys
from sqlalchemy import create_engine
from dotenv import load_dotenv
from scrapyProductos import scrapear_yapo

# Cargar variables de entorno
load_dotenv('.env')
load_dotenv('config.env', override=True)

# Conexión a la base de datos
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'tu_contraseña')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'alquimia')

DATABASE_URL = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(DATABASE_URL)

# ========== CONFIGURACIÓN ==========
CARPETA = "archivos"
os.makedirs(CARPETA, exist_ok=True)

# ========== TIENDAS PREDEFINIDAS ==========
TIENDAS_DISPONIBLES = {
    '1': {'url': 'https://www.yapo.cl', 'nombre': 'Yapo'},
    '2': {'url': 'https://listado.mercadolibre.cl', 'nombre': 'MercadoLibre'}, 
    '3': {'url': 'https://www.paris.cl', 'nombre': 'Paris'},
    '4': {'url': 'https://www.falabella.com', 'nombre': 'Falabella'}
}

# ========== PATRONES DE PRECIOS ==========
patron_precio = r'\$\s*[\d,]+(?:\.\d{3})*(?:,\d{2})?|\d+(?:\.\d{3})*(?:,\d{2})?\s*(?:pesos|clp|\$)'

# ========== RANGOS ETARIOS Y PREFERENCIAS ==========
RANGOS_ETARIOS = {
    '18-25': {'min_edad': 18, 'max_edad': 25, 'preferencias': ['tecnologia', 'ropa', 'deportes']},
    '26-35': {'min_edad': 26, 'max_edad': 35, 'preferencias': ['tecnologia', 'hogar', 'ropa']},
    '36-45': {'min_edad': 36, 'max_edad': 45, 'preferencias': ['hogar', 'tecnologia', 'libros']},
    '46-55': {'min_edad': 46, 'max_edad': 55, 'preferencias': ['hogar', 'libros', 'deportes']},
    '56+': {'min_edad': 56, 'max_edad': 80, 'preferencias': ['libros', 'hogar', 'deportes']}
}

def mostrar_menu_tiendas():
    """Muestra el listado de tiendas disponibles"""
    print("\n🏪 TIENDAS DISPONIBLES:")
    print("=" * 30)
    for key, tienda in TIENDAS_DISPONIBLES.items():
        print(f"{key}. {tienda['nombre']}")
    print("0. Volver atrás")
    print("=" * 30)

def seleccionar_tienda():
    """Selecciona una tienda del listado"""
    while True:
        mostrar_menu_tiendas()
        opcion = input("Selecciona una opción (0-4): ").strip()
        
        if opcion == '0':
            print("👋 ¡Hasta luego!")
            sys.exit(0)
        
        elif opcion in TIENDAS_DISPONIBLES:
            return TIENDAS_DISPONIBLES[opcion]
        
        else:
            print("❌ Opción no válida")

def generar_usuarios_con_edad(cantidad):
    """Genera usuarios con edad y sexo usando RandomUser API"""
    print(f"👥 Generando {cantidad} usuarios...")
    
    url = f"https://randomuser.me/api/?results={cantidad}&nat=cl"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("❌ Error al conectar con RandomUser API")
        return []
    
    data = response.json()["results"]
    usuarios = []
    
    for user in data:
        edad = str(user["dob"]["age"])
        sexo = "Masculino" if user["gender"] == "male" else "Femenino"
        
        usuarios.append({
            "id_usuario": len(usuarios) + 1,
            "nombre": user["name"]["first"],
            "apellido": user["name"]["last"],
            "email": user["email"],
            "edad": edad,
            "sexo": sexo
        })
    
    print(f"✅ {len(usuarios)} usuarios generados exitosamente")
    return usuarios

def extraer_direccion_tienda(url_tienda):
    """Extrae información de dirección de la tienda"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url_tienda, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar información de contacto/dirección
        direccion_texto = ""
        
        # Buscar en elementos comunes de dirección
        elementos_direccion = soup.find_all(['p', 'div', 'span'], 
                                          string=re.compile(r'(dirección|direccion|address|ubicación|sucursal)', re.I))
        
        for elemento in elementos_direccion:
            texto = elemento.get_text(strip=True)
            if len(texto) > 10 and len(texto) < 200:
                direccion_texto = texto
                break
        
        # Si no encuentra, buscar en footer
        if not direccion_texto:
            footer = soup.find('footer')
            if footer:
                direccion_texto = footer.get_text(strip=True)[:100]
        
        return direccion_texto if direccion_texto else "Dirección no disponible"
        
    except Exception as e:
        print(f"⚠️ Error al extraer dirección: {e}")
        return "Dirección no disponible"

def scrapear_productos_con_promociones(url_tienda, termino_busqueda, cantidad):
    """Scraping de productos con información de promociones"""
    print(f"🛍️ Scraping productos '{termino_busqueda}' en {url_tienda}...")
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # Detectar método de búsqueda
    try:
        response = requests.get(url_tienda, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar formulario de búsqueda
        formulario = soup.find('form')
        if formulario:
            inputs = formulario.find_all('input')
            for inp in inputs:
                if inp.get('type') in ['text', 'search']:
                    parametro = inp.get('name', 'q')
                    break
            else:
                parametro = 'q'
        else:
            parametro = 'q'
        
        # Construir URL de búsqueda
        if '?' in url_tienda:
            url_busqueda = f"{url_tienda}&{parametro}={termino_busqueda}"
        else:
            url_busqueda = f"{url_tienda}?{parametro}={termino_busqueda}"
        
        # Realizar búsqueda
        response = requests.get(url_busqueda, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        productos = []
        
        # Buscar productos en diferentes selectores comunes
        selectores_productos = [
            'div[class*="product"]', 'div[class*="item"]', 'div[class*="card"]',
            'article', 'li[class*="product"]', 'div[class*="listing"]'
        ]
        
        for selector in selectores_productos:
            elementos = soup.select(selector)
            if elementos:
                break
        
        for i, elemento in enumerate(elementos[:cantidad]):
            try:
                # Extraer nombre del producto
                nombre_elem = elemento.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or elemento.find(class_=re.compile(r'title|name|product'))
                nombre = nombre_elem.get_text(strip=True) if nombre_elem else f"Producto {i+1}"
                
                # Extraer precio
                precio_elem = elemento.find(string=re.compile(patron_precio)) or elemento.find(class_=re.compile(r'price|precio'))
                precio_texto = precio_elem if isinstance(precio_elem, str) else precio_elem.get_text(strip=True) if precio_elem else "0"
                precio = limpiar_precio(precio_texto)
                
                # Extraer descuento/promoción
                descuento_elem = elemento.find(string=re.compile(r'%|descuento|oferta|promoción', re.I)) or elemento.find(class_=re.compile(r'discount|descuento|oferta'))
                descuento_texto = descuento_elem if isinstance(descuento_elem, str) else descuento_elem.get_text(strip=True) if descuento_elem else "0"
                descuento = limpiar_descuento(descuento_texto)
                
                # Calcular precio final
                precio_final = precio - descuento if precio and descuento else precio
                
                # Extraer URL del producto
                link_elem = elemento.find('a', href=True)
                url_producto = urljoin(url_tienda, link_elem['href']) if link_elem else ""
                
                productos.append({
                    "id_producto": len(productos) + 1,
                    "nombre": nombre,
                    "marca": extraer_marca(nombre),
                    "precio": precio,
                    "url_producto": url_producto,
                    "promocion": descuento,
                    "preciofinal": precio_final,
                    "id_tienda": None  # Se asignará después
                })
                
            except Exception as e:
                print(f"⚠️ Error al procesar producto {i+1}: {e}")
                continue
        
        print(f"✅ {len(productos)} productos encontrados")
        return productos
        
    except Exception as e:
        print(f"❌ Error en scraping: {e}")
        return []

def extraer_marca(nombre_producto):
    """Extrae la marca del nombre del producto"""
    marcas_comunes = ['Samsung', 'Apple', 'Sony', 'LG', 'Nike', 'Adidas', 'Puma', 'Reebok', 
                     'Nintendo', 'PlayStation', 'Xbox', 'Canon', 'Nikon', 'HP', 'Dell', 'Lenovo']
    
    for marca in marcas_comunes:
        if marca.lower() in nombre_producto.lower():
            return marca
    
    return "Sin marca"

def limpiar_precio(precio_texto):
    """Limpia y convierte el precio a número"""
    if not precio_texto:
        return 0
    
    # Extraer solo números y punto decimal
    precio_limpio = re.sub(r'[^\d.,]', '', precio_texto)
    
    # Manejar diferentes formatos de números
    if ',' in precio_limpio and '.' in precio_limpio:
        # Formato: 1.234,56
        precio_limpio = precio_limpio.replace('.', '').replace(',', '.')
    elif ',' in precio_limpio:
        # Formato: 1,234
        if precio_limpio.count(',') == 1 and len(precio_limpio.split(',')[1]) <= 2:
            precio_limpio = precio_limpio.replace(',', '.')
        else:
            precio_limpio = precio_limpio.replace(',', '')
    
    try:
        return float(precio_limpio) if precio_limpio else 0
    except:
        return 0

def limpiar_descuento(descuento_texto):
    """Limpia y convierte el descuento a número"""
    if not descuento_texto:
        return 0
    
    # Buscar porcentaje
    porcentaje = re.search(r'(\d+)%', descuento_texto)
    if porcentaje:
        return float(porcentaje.group(1))
    
    # Buscar números
    numero = re.search(r'(\d+(?:\.\d+)?)', descuento_texto)
    if numero:
        return float(numero.group(1))
    
    return 0

def generar_promociones(productos):
    """Genera promociones basadas en los productos con descuentos"""
    print("🎯 Generando promociones...")
    
    promociones = []
    tipos_promocion = ["Descuento por porcentaje", "Oferta especial", "Precio rebajado", "Cyber Monday", "Black Friday"]
    
    for i, producto in enumerate(productos):
        if producto['promocion'] > 0:
            # Generar fechas de promoción (últimos 3 meses)
            fecha_inicio = datetime.now() - timedelta(days=random.randint(30, 90))
            fecha_fin = fecha_inicio + timedelta(days=random.randint(7, 30))
            
            promociones.append({
                "id_promocion": len(promociones) + 1,
                "tipo_promocion": random.choice(tipos_promocion),
                "fecha_inicio": fecha_inicio.date(),
                "fecha_fin": fecha_fin.date()
            })
    
    print(f"✅ {len(promociones)} promociones generadas")
    return promociones

def generar_tiempo(promociones):
    """Genera registros de tiempo basados en las fechas de promociones"""
    print("⏰ Generando registros de tiempo...")
    
    fechas_unicas = set()
    
    # Agregar fechas de promociones
    for promocion in promociones:
        fechas_unicas.add(promocion['fecha_inicio'])
        fechas_unicas.add(promocion['fecha_fin'])
    
    # Agregar fechas adicionales (últimos 6 meses)
    fecha_actual = datetime.now()
    for i in range(180):
        fecha = fecha_actual - timedelta(days=i)
        fechas_unicas.add(fecha.date())
    
    tiempo_registros = []
    festivos_chile = [
        datetime(2024, 1, 1).date(),  # Año Nuevo
        datetime(2024, 5, 1).date(),  # Día del Trabajo
        datetime(2024, 9, 18).date(), # Fiestas Patrias
        datetime(2024, 12, 25).date() # Navidad
    ]
    
    for i, fecha in enumerate(sorted(fechas_unicas)):
        tiempo_registros.append({
            "id_tiempo": i + 1,
            "fecha": fecha,
            "dia": fecha.day,
            "mes": fecha.month,
            "año": fecha.year,
            "trimestre": (fecha.month - 1) // 3 + 1,
            "festivo": fecha in festivos_chile
        })
    
    print(f"✅ {len(tiempo_registros)} registros de tiempo generados")
    return tiempo_registros

def simular_ventas_realistas(usuarios, productos, promociones, tiempo_registros):
    """Simula ventas realistas basadas en rangos etarios"""
    print("💰 Simulando ventas realistas...")
    
    ventas = []
    
    for usuario in usuarios:
        edad = int(usuario['edad'])
        
        # Determinar rango etario
        rango_etario = None
        for rango, config in RANGOS_ETARIOS.items():
            if config['min_edad'] <= edad <= config['max_edad']:
                rango_etario = config
                break
        
        if not rango_etario:
            rango_etario = RANGOS_ETARIOS['26-35']  # Default
        
        # Número de compras por usuario (1-5)
        num_compras = random.randint(1, 5)
        
        for _ in range(num_compras):
            # Seleccionar producto (con preferencias por rango etario)
            producto = random.choice(productos)
            
            # Seleccionar fecha de venta
            fecha_venta = random.choice(tiempo_registros)
            
            # Determinar si aplica promoción
            promocion_aplicada = None
            if producto['promocion'] is not None: # Check if it's not None
                promociones_disponibles = [p for p in promociones if 
                                         p['fecha_inicio'] <= fecha_venta['fecha'] <= p['fecha_fin']]
                if promociones_disponibles:
                    promocion_aplicada = random.choice(promociones_disponibles)
            
            # Cantidad vendida (1-3)
            cantidad = random.randint(1, 3)
            
            # Precios
            precio_unitario = producto['precio'] or random.randint(10000, 100000)
            descuento_unitario = producto['promocion'] or 0
            precio_final_unitario = precio_unitario - descuento_unitario
            
            # Totales
            total_bruto = precio_unitario * cantidad
            total_descuento = descuento_unitario * cantidad
            total_neto = precio_final_unitario * cantidad
            
            ventas.append({
                "id_venta": len(ventas) + 1,
                "id_usuario": usuario['id_usuario'],
                "id_producto": producto['id_producto'],
                "id_tienda": producto['id_tienda'],
                "id_tiempo": fecha_venta['id_tiempo'],
                "id_promocion": promocion_aplicada['id_promocion'] if promocion_aplicada else None,
                "cantidad_vendida": cantidad,
                "precio_unitario": precio_unitario,
                "descuento_unitario": descuento_unitario,
                "precio_final_unitario": precio_final_unitario,
                "total_bruto": total_bruto,
                "total_descuento": total_descuento,
                "total_neto": total_neto
            })
    
    print(f"✅ {len(ventas)} ventas simuladas")
    return ventas

def generar_archivo_completo(usuarios, productos, promociones, tiempo_registros, ventas, tienda_info, nombre_archivo):
    """Genera un archivo CSV y Excel con todos los datos integrados, sin IDs, solo datos descriptivos y de referencia"""
    print("📊 Generando archivo completo...")
    datos_completos = []
    for venta in ventas:
        usuario = next((u for u in usuarios if u['id_usuario'] == venta['id_usuario']), {})
        producto = next((p for p in productos if p['id_producto'] == venta['id_producto']), {})
        promocion = next((p for p in promociones if p['id_promocion'] == venta['id_promocion']), {}) if venta['id_promocion'] else {}
        tiempo = next((t for t in tiempo_registros if t['id_tiempo'] == venta['id_tiempo']), {})
        registro = {
            # Usuario
            'nombre_usuario': usuario.get('nombre'),
            'apellido_usuario': usuario.get('apellido'),
            'email_usuario': usuario.get('email'),
            'edad_usuario': usuario.get('edad'),
            'sexo_usuario': usuario.get('sexo'),
            # Tienda
            'nombre_tienda': tienda_info.get('nombre'),
            'direccion_tienda': tienda_info.get('direccion'),
            'url_tienda': tienda_info.get('url'),
            # Producto
            'nombre_producto': producto.get('nombre'),
            'marca_producto': producto.get('marca'),
            'precio_producto': producto.get('precio'),
            'url_producto': producto.get('url_producto'),
            # Promoción
            'tipo_promocion': promocion.get('tipo_promocion'),
            'fecha_inicio_promocion': promocion.get('fecha_inicio'),
            'fecha_fin_promocion': promocion.get('fecha_fin'),
            # Tiempo
            'fecha_venta': tiempo.get('fecha'),
            'dia_venta': tiempo.get('dia'),
            'mes_venta': tiempo.get('mes'),
            'año_venta': tiempo.get('año'),
            'trimestre_venta': tiempo.get('trimestre'),
            'festivo_venta': tiempo.get('festivo'),
            # Venta
            'cantidad_vendida': venta.get('cantidad_vendida'),
            'precio_unitario': venta.get('precio_unitario'),
            'descuento_unitario': venta.get('descuento_unitario'),
            'precio_final_unitario': venta.get('precio_final_unitario'),
            'total_bruto': venta.get('total_bruto'),
            'total_descuento': venta.get('total_descuento'),
            'total_neto': venta.get('total_neto')
        }
        datos_completos.append(registro)
    df = pd.DataFrame(datos_completos)
    csv_filename = os.path.join(CARPETA, f"{nombre_archivo}.csv")
    excel_filename = os.path.join(CARPETA, f"{nombre_archivo}.xlsx")
    df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
    df.to_excel(excel_filename, index=False)
    print(f"✅ Archivos generados exitosamente:")
    print(f"   📄 CSV: {csv_filename}")
    print(f"   📊 Excel: {excel_filename}")
    print(f"   📊 Total de registros: {len(datos_completos)}")
    return df

def main():
    """Función principal del scraper integrado"""
    print("🚀 SCRAPER INTEGRADO - GENERADOR DE DATOS COMPLETOS")
    print("=" * 60)
    
    # Solicitar parámetros
    try:
        cantidad_usuarios = int(input("👥 Ingrese cantidad de usuarios a generar: "))
        if cantidad_usuarios <= 0:
            print("❌ La cantidad debe ser mayor a 0")
            return
    except ValueError:
        print("❌ Por favor ingrese un número válido")
        return
    
    # Seleccionar tienda
    tienda_seleccionada = seleccionar_tienda()
    
    # Extraer información de la tienda
    print(f"\n🏪 Extrayendo información de la tienda: {tienda_seleccionada['nombre']}")
    direccion_tienda = extraer_direccion_tienda(tienda_seleccionada['url'])
    
    # Crear información de tienda
    tienda_info = {
        'id_tienda': 1,
        'nombre': tienda_seleccionada['nombre'],
        'direccion': direccion_tienda,
        'url': tienda_seleccionada['url']
    }
    
    print(f"✅ Información de tienda extraída:")
    print(f"   🏪 Nombre: {tienda_info['nombre']}")
    print(f"   📍 Dirección: {tienda_info['direccion']}")
    print(f"   🌐 URL: {tienda_info['url']}")
    
    # Solicitar término de búsqueda
    termino_busqueda = input("🔍 Ingrese término de búsqueda para productos: ").strip()
    if not termino_busqueda:
        print("❌ Debe ingresar un término de búsqueda")
        return
    
    # Solicitar cantidad de productos
    try:
        cantidad_productos = int(input("🛍️ Ingrese cantidad de productos a buscar: "))
        if cantidad_productos <= 0:
            print("❌ La cantidad debe ser mayor a 0")
            return
    except ValueError:
        print("❌ Por favor ingrese un número válido")
        return
    
    # Solicitar nombre del archivo
    nombre_archivo = input("📁 Ingrese nombre del archivo (sin extensión): ").strip()
    if not nombre_archivo:
        nombre_archivo = f"datos_completos_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print("\n🔄 Iniciando proceso de generación de datos...")
    
    # 1. Generar usuarios
    usuarios = generar_usuarios_con_edad(cantidad_usuarios)
    
    # 2. Scraping de productos
    if tienda_seleccionada['nombre'].lower() == 'yapo':
        productos_raw = scrapear_yapo(termino_busqueda, cantidad_productos)
        productos = []
        promociones = []
        promo_id_counter = 1
        for i, prod in enumerate(productos_raw):
            promo_id = None
            # Si el producto tiene descuento real, crear promoción
            if prod.get('descuento') and prod.get('descuento') > 0:
                # Usar la fecha actual como inicio y fin (puedes mejorar esto si el scraping trae fechas)
                fecha_inicio = datetime.now().date()
                fecha_fin = fecha_inicio + timedelta(days=30)
                promociones.append({
                    "id_promocion": promo_id_counter,
                    "tipo_promocion": "Descuento real Yapo",
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin
                })
                promo_id = promo_id_counter
                promo_id_counter += 1
            productos.append({
                "id_producto": i + 1,
                "nombre": prod.get('nombre', ''),
                "marca": prod.get('marca', ''),
                "precio": prod.get('precio', 0),
                "url_producto": prod.get('url_producto', ''),
                "promocion": promo_id,
                "preciofinal": prod.get('preciofinal', 0),
                "id_tienda": 1  # Yapo
            })
    else:
        productos = scrapear_productos_con_promociones(
            tienda_seleccionada['url'], 
            termino_busqueda, 
            cantidad_productos
        )
        promociones = []
        promo_id_counter = 1
        for producto in productos:
            promo_id = None
            if producto.get('promocion') and producto.get('promocion') > 0:
                fecha_inicio = datetime.now().date()
                fecha_fin = fecha_inicio + timedelta(days=30)
                promociones.append({
                    "id_promocion": promo_id_counter,
                    "tipo_promocion": "Descuento real",
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin
                })
                promo_id = promo_id_counter
                promo_id_counter += 1
            producto['promocion'] = promo_id
            producto['id_tienda'] = tienda_info['id_tienda']
    
    # 3. Generar tiempo
    tiempo_registros = generar_tiempo(promociones)
    
    # 4. Simular ventas
    ventas = simular_ventas_realistas(usuarios, productos, promociones, tiempo_registros)
    
    # 5. Generar archivo completo
    df_final = generar_archivo_completo(
        usuarios, productos, promociones, tiempo_registros, ventas, tienda_info, nombre_archivo
    )
    
    print("\n🎉 ¡Proceso completado exitosamente!")
    print(f"📊 Se generaron {len(df_final)} registros completos")
    print(f"👥 {len(usuarios)} usuarios")
    print(f"🏪 {tienda_info['nombre']} (ID: {tienda_info['id_tienda']})")
    print(f"🛍️ {len(productos)} productos")
    print(f"🎯 {len(promociones)} promociones")
    print(f"⏰ {len(tiempo_registros)} registros de tiempo")
    print(f"💰 {len(ventas)} ventas simuladas")

if __name__ == "__main__":
    main() 