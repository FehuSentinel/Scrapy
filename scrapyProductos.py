# UNIVERSAL PRODUCT SCRAPER INTELIGENTE
import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd
import os
from urllib.parse import urlparse, urljoin, quote_plus
import re
from difflib import get_close_matches
import json
import time
import sys
from sqlalchemy import create_engine
from dotenv import load_dotenv

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
patron_precio = r'\$\s*[\d,]+(?:\.\d{3})*(?:,\d{2})?|\d+(?:\.\d{3})*(?:,\d{2})?\s*(?:pesos|clp|\$)'

# ========== TIENDAS PREDEFINIDAS ==========
TIENDAS_DISPONIBLES = {
    '1': 'https://www.yapo.cl',
    '2': 'https://listado.mercadolibre.cl', 
    '3': 'https://www.paris.cl',
    '4': 'https://www.falabella.com'
}

def mostrar_menu_tiendas():
    """Muestra el listado simple de tiendas"""
    print("\n🏪 TIENDAS DISPONIBLES:")
    print("=" * 30)
    print("1. Yapo")
    print("2. MercadoLibre") 
    print("3. Paris")
    print("4. Falabella")
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

def limpiar_texto(texto):
    """Limpia y normaliza texto"""
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto.strip())

def extraer_nombre_tienda(url):
    """Extrae el nombre de la tienda de la URL"""
    dominio = urlparse(url).netloc
    return dominio.replace('www.', '').split('.')[0].title()

def detectar_metodo_busqueda(url):
    """Detecta automáticamente cómo buscar productos en el sitio"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error al acceder al sitio: {e}")
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Buscar formularios de búsqueda en la página principal
    formularios = soup.find_all('form')
    for form in formularios:
        inputs = form.find_all('input')
        for inp in inputs:
            input_type = inp.get('type', '').lower()
            input_name = inp.get('name', '').lower()
            input_id = inp.get('id', '').lower()
            input_placeholder = inp.get('placeholder', '').lower()
            input_class = inp.get('class', [])
            if input_class:
                input_class = ' '.join(input_class).lower()
            
            # Detectar si es un campo de búsqueda
            es_busqueda = False
            
            # Criterio 1: Tipo de input
            if input_type in ['text', 'search']:
                es_busqueda = True
            
            # Criterio 2: Nombre del campo
            if any(x in input_name for x in ['search', 'q', 'query', 'buscar', 'busqueda', 'keyword', 'term']):
                es_busqueda = True
            
            # Criterio 3: ID del campo
            if any(x in input_id for x in ['search', 'q', 'query', 'buscar', 'busqueda', 'keyword', 'term']):
                es_busqueda = True
            
            # Criterio 4: Placeholder
            if any(x in input_placeholder for x in ['buscar', 'search', 'encontrar', 'producto', 'qué buscas', 'what are you looking for']):
                es_busqueda = True
            
            # Criterio 5: Clase CSS
            if any(x in input_class for x in ['search', 'buscar', 'query', 'keyword']):
                es_busqueda = True
            
            if es_busqueda:
                action = form.get('action', '')
                method = form.get('method', 'get').lower()
                
                # Construir URL de búsqueda
                if action.startswith('http'):
                    base_search_url = action
                elif action.startswith('/'):
                    base_search_url = urljoin(url, action)
                else:
                    base_search_url = url
                
                # Verificar que la URL no sea de servicios o promociones
                url_lower = base_search_url.lower()
                if any(x in url_lower for x in ['despacho', 'gratis', 'oferta', 'promocion', 'cyber', 'black', 'page/', 'servicio', 'ayuda', 'contacto']):
                    continue
                
                parametro = inp.get('name', 'q')
                print(f"🔍 Campo de búsqueda detectado: {parametro}")
                print(f"📝 Método: {method}")
                print(f"🌐 URL base: {base_search_url}")
                
                return base_search_url, parametro
    
    # Si no encuentra formulario, buscar enlaces de búsqueda
    enlaces = soup.find_all('a', href=True)
    for enlace in enlaces:
        href = enlace['href'].lower()
        texto = enlace.get_text(strip=True).lower()
        
        # Buscar enlaces de búsqueda específicos
        if any(x in href for x in ['/search', '/buscar', '/find', '/productos', '/items']) or \
           any(x in texto for x in ['buscar', 'search', 'encontrar', 'productos']):
            
            # Verificar que no sea de servicios
            if not any(x in href for x in ['despacho', 'gratis', 'oferta', 'promocion', 'cyber', 'black', 'page/', 'servicio', 'ayuda', 'contacto']):
                return urljoin(url, enlace['href']), 'q'
    
    # Buscar barra de búsqueda en el header/navbar
    print("🔍 Buscando barra de búsqueda en header...")
    
    # Buscar en elementos de navegación
    nav_elements = soup.find_all(['nav', 'header', 'div'], class_=lambda x: x and any(word in x.lower() for word in ['nav', 'header', 'search', 'buscar']))
    
    for nav in nav_elements:
        # Buscar formularios de búsqueda en navegación
        forms = nav.find_all('form')
        for form in forms:
            inputs = form.find_all('input')
            for inp in inputs:
                input_type = inp.get('type', '').lower()
                input_name = inp.get('name', '').lower()
                input_placeholder = inp.get('placeholder', '').lower()
                
                if (input_type in ['text', 'search'] or
                    any(x in input_name for x in ['search', 'q', 'query', 'buscar', 'busqueda']) or
                    any(x in input_placeholder for x in ['buscar', 'search', 'encontrar', 'producto'])):
                    
                    action = form.get('action', '')
                    if action.startswith('http'):
                        base_search_url = action
                    elif action.startswith('/'):
                        base_search_url = urljoin(url, action)
                    else:
                        base_search_url = url
                    
                    # Verificar que no sea de servicios
                    url_lower = base_search_url.lower()
                    if any(x in url_lower for x in ['despacho', 'gratis', 'oferta', 'promocion', 'cyber', 'black', 'page/', 'servicio', 'ayuda', 'contacto']):
                        continue
                    
                    parametro = inp.get('name', 'q')
                    print(f"🔍 Campo de búsqueda detectado en header: {parametro}")
                    print(f"🌐 URL base: {base_search_url}")
                    
                    return base_search_url, parametro
    
    # Método por defecto: búsqueda en URL principal
    print("⚠️ No se detectó formulario de búsqueda específico, usando búsqueda por URL")
    return url, 'q'

def corregir_busqueda(termino_busqueda):
    """Corrige y normaliza el término de búsqueda"""
    # Palabras comunes que se pueden corregir
    correcciones = {
        'celular': ['celulares', 'telefono', 'telefonos', 'smartphone', 'smartphones'],
        'laptop': ['laptops', 'notebook', 'notebooks', 'portatil', 'portatiles'],
        'auto': ['autos', 'carro', 'carros', 'vehiculo', 'vehiculos'],
        'casa': ['casas', 'departamento', 'departamentos', 'inmueble', 'inmuebles'],
        'ropa': ['vestimenta', 'prendas', 'moda'],
        'zapatilla': ['zapatillas', 'tenis', 'calzado', 'zapatos'],
        'tv': ['televisor', 'televisores', 'television'],
        'refrigerador': ['refrigeradores', 'heladera', 'heladeras', 'frigorifico'],
        'mueble': ['muebles', 'mobiliario'],
        'juguete': ['juguetes', 'juego', 'juegos'],
        'crema': ['cremas', 'loción', 'lociones', 'hidratante', 'hidratantes'],
        'perfume': ['perfumes', 'fragancia', 'fragancias', 'colonia', 'colonias']
    }
    
    termino_lower = termino_busqueda.lower()
    
    # Buscar correcciones
    for palabra_correcta, variantes in correcciones.items():
        if termino_lower in variantes or termino_lower == palabra_correcta:
            return palabra_correcta
    
    # Si no encuentra corrección, devolver el término original
    return termino_busqueda

def detectar_productos_universal(soup, url_base):
    """Detecta productos usando estrategias universales"""
    print("🔍 Analizando estructura de productos...")
    
    productos = []
    
    # Lista extensa de palabras que NO son productos
    palabras_excluir = [
        # Navegación
        'buscar', 'carrito', 'compras', 'vender', 'ayuda', 'contacto', 
        'inicio', 'login', 'registro', 'saltar', 'comentar', 'accesibilidad',
        'politica', 'terminos', 'condiciones', 'privacidad', 'cookies',
        'mapa', 'sitemap', 'rss', 'feed', 'blog', 'noticia', 'novedad',
        
        # Promociones y marketing
        'compra online', 'retira', 'despacho', 'gratis', 'oferta', 'descuento',
        'promoción', 'promocion', 'cyber', 'black friday', 'liquidación',
        'envío', 'envio', 'entrega', 'pickup', 'retiro',
        
        # Cuentas y usuarios
        'crear cuenta', 'mi cuenta', 'olvidaste', 'contraseña', 'password',
        'registrarse', 'inscribirse', 'club', 'beneficios', 'mi perfil',
        
        # Información del sitio
        'sobre nosotros', 'quienes somos', 'nuestra empresa', 'historia',
        'trabaja con nosotros', 'empleos', 'carreras', 'prensa', 'medios',
        
        # Servicios
        'servicio al cliente', 'postventa', 'garantía', 'garantia', 'devolución',
        'cambio', 'reembolso', 'soporte', 'ayuda', 'faq', 'preguntas',
        
        # Legal
        'términos', 'terminos', 'condiciones', 'política', 'politica',
        'privacidad', 'cookies', 'legal', 'aviso', 'disclaimer',
        
        # Categorías y navegación
        'ir a pagar', 'cuidado de la piel', 'cosmética', 'protección',
        'multipropósito', 'categoría', 'categoria', 'ver más', 'ver todo'
    ]
    
    # URLs que NO son productos
    urls_excluir = [
        '/cart', '/login', '/register', '/help', '/contact', '/about', 
        '/policy', '/terms', '/privacy', '/cookies', '/legal', '/sitemap',
        '/blog', '/news', '/press', '/careers', '/jobs', '/support',
        '/account', '/profile', '/password', '/reset', '/forgot',
        '/club', '/benefits', '/loyalty', '/rewards', '/points',
        '/bolsa', '/carrito', '/checkout', '/pagar'
    ]
    
    # URLs que SÍ son productos (contienen IDs o códigos)
    urls_producto = [
        '/product/', '/item/', '/p/', '/prod/', '/producto/',
        '/mlc/', '/mercadolibre/', '/detail/', '/detalle/'
    ]
    
    # Estrategia 1: Buscar enlaces que parecen productos específicos
    enlaces = soup.find_all('a', href=True)
    enlaces_productos = []
    
    for enlace in enlaces:
        href = enlace['href'].lower()
        texto = enlace.get_text(strip=True)
        
        # Verificar que el enlace parezca un producto específico
        es_producto = False
        
        # Criterio 1: URL contiene patrones de productos
        if any(x in href for x in urls_producto):
            es_producto = True
        
        # Criterio 2: URL contiene ID numérico (típico de productos)
        if re.search(r'/\d+', href):
            es_producto = True
        
        # Criterio 3: URL contiene código de producto
        if re.search(r'/[a-z0-9]{6,}', href):
            es_producto = True
        
        # Criterio 4: Texto parece nombre de producto específico
        if (len(texto) > 8 and  # Mínimo 8 caracteres
            len(texto.split()) >= 3 and  # Al menos 3 palabras
            not any(x in texto.lower() for x in palabras_excluir) and
            not any(x in href for x in urls_excluir) and
            not href.startswith('#') and
            not href.startswith('javascript:') and
            not href.startswith('mailto:') and
            not href.startswith('tel:') and
            # Verificar que no sea solo texto promocional
            not re.search(r'[😱🎉🔥💥]', texto) and  # Emojis promocionales
            not re.search(r'\$\d+\.?\d*\s*(?:gratis|envío|despacho)', texto, re.IGNORECASE) and
            # Verificar que parezca un nombre de producto
            not texto.isupper() and  # No todo en mayúsculas
            not texto.endswith('?') and  # No preguntas
            not texto.endswith('!') and  # No exclamaciones
            # Verificar que no sea categoría
            not any(x in texto.lower() for x in ['categoría', 'categoria', 'ver más', 'ver todo', 'ir a pagar'])):
            es_producto = True
        
        if es_producto:
            enlaces_productos.append(enlace)
    
    print(f"📦 Encontrados {len(enlaces_productos)} enlaces de productos específicos...")
    
    # Estrategia 2: Buscar elementos con estructura de producto específico
    elementos_producto = []
    
    # Buscar elementos que contengan información específica de productos
    for elemento in soup.find_all(['div', 'article', 'li', 'section']):
        enlaces_internos = elemento.find_all('a', href=True)
        texto = elemento.get_text(strip=True)
        
        # Verificar que contenga información específica de producto
        tiene_info_producto = False
        
        # Criterio 1: Tiene precio
        if re.search(r'\$[\d,]+', texto):
            tiene_info_producto = True
        
        # Criterio 2: Tiene especificaciones técnicas
        if re.search(r'\d+\s*(?:ml|g|kg|cm|m|w|v|oz|lbs)', texto, re.IGNORECASE):
            tiene_info_producto = True
        
        # Criterio 3: Tiene código de producto
        if re.search(r'[A-Z]{2,}\d{3,}|[A-Z0-9]{6,}', texto):
            tiene_info_producto = True
        
        # Criterio 4: Tiene descripción detallada
        if len(texto.split()) >= 8 and not any(x in texto.lower() for x in palabras_excluir):
            tiene_info_producto = True
        
        # Si tiene enlaces y información de producto
        if (len(enlaces_internos) > 0 and 
            len(texto) > 20 and  # Más texto para ser más estricto
            not any(x in texto.lower() for x in palabras_excluir) and
            tiene_info_producto):
            
            elementos_producto.append(elemento)
    
    print(f"📦 Encontrados {len(elementos_producto)} elementos con información de producto...")
    
    # Combinar ambas estrategias
    todos_elementos = enlaces_productos + elementos_producto
    
    return todos_elementos

def extraer_datos_universal(elemento, url_base):
    """Extrae datos de un producto usando estrategias universales"""
    datos = {
        'nombre': '',
        'marca': '',
        'precio': '',
        'tienda': extraer_nombre_tienda(url_base),
        'url_producto': ''
    }
    
    # Si es un enlace directo
    if elemento.name == 'a':
        datos['nombre'] = limpiar_texto(elemento.get_text())
        href = elemento['href']
        if href.startswith('http'):
            datos['url_producto'] = href
        else:
            datos['url_producto'] = urljoin(url_base, href)
    else:
        # Si es un contenedor, buscar el enlace principal
        enlaces = elemento.find_all('a', href=True)
        if enlaces:
            enlace_principal = enlaces[0]
            datos['nombre'] = limpiar_texto(enlace_principal.get_text())
            href = enlace_principal['href']
            if href.startswith('http'):
                datos['url_producto'] = href
            else:
                datos['url_producto'] = urljoin(url_base, href)
    
    # Buscar precio en todo el texto del elemento
    texto_completo = elemento.get_text()
    
    # Patrones de precio más flexibles y específicos
    patrones_precio = [
        r'\$\s*[\d,]+(?:\.\d{2})?',  # $1,234.56
        r'\$\s*\d+(?:\.\d{3})*(?:,\d{2})?',  # $1.234,56
        r'\d+(?:\.\d{3})*(?:,\d{2})?\s*(?:pesos|clp|usd)',  # 1.234,56 pesos
        r'\d+(?:\.\d{3})*(?:,\d{2})?\s*\$',  # 1.234,56 $
        r'\$\s*\d+(?:\.\d{3})*(?:,\d{2})?',  # $1.234,56
        r'\d+(?:\.\d{3})*(?:,\d{2})?',  # 1.234,56 (solo números)
        r'\$\s*\d+',  # $1234
        r'\d+\s*\$',  # 1234 $
        r'\d+\s*(?:pesos|clp|usd)',  # 1234 pesos
        r'precio:\s*\$\s*[\d,]+',  # precio: $1,234
        r'valor:\s*\$\s*[\d,]+',  # valor: $1,234
    ]
    
    for patron in patrones_precio:
        match = re.search(patron, texto_completo, re.IGNORECASE)
        if match:
            datos['precio'] = match.group().strip()
            break
    
    # Extraer marca del nombre (primera palabra)
    if datos['nombre']:
        palabras = datos['nombre'].split()
        if palabras:
            datos['marca'] = palabras[0]
    
    return datos

def extraer_datos_producto_resultado(elemento, url_base):
    """Extrae datos de un producto de la página de resultados"""
    datos = {
        'nombre': '',
        'marca': '',
        'precio': '',
        'tienda': extraer_nombre_tienda(url_base),
        'url_producto': ''
    }
    
    # Si es un enlace directo
    if elemento.name == 'a':
        datos['nombre'] = limpiar_texto(elemento.get_text())
        href = elemento['href']
        if href.startswith('http'):
            datos['url_producto'] = href
        else:
            datos['url_producto'] = urljoin(url_base, href)
    else:
        # Si es un contenedor, buscar el enlace principal
        enlaces = elemento.find_all('a', href=True)
        if enlaces:
            enlace_principal = enlaces[0]
            datos['nombre'] = limpiar_texto(enlace_principal.get_text())
            href = enlace_principal['href']
            if href.startswith('http'):
                datos['url_producto'] = href
            else:
                datos['url_producto'] = urljoin(url_base, href)
    
    # Buscar precio en el elemento
    texto_completo = elemento.get_text()
    precio_match = re.search(r'\$[\d,]+|\d+\.\d+\s*(?:USD|CLP|EUR)|\d+\s*(?:pesos|dólares|euros)', texto_completo, re.IGNORECASE)
    if precio_match:
        datos['precio'] = precio_match.group()
    
    # Extraer marca del nombre (primera palabra)
    if datos['nombre']:
        palabras = datos['nombre'].split()
        if palabras:
            datos['marca'] = palabras[0]
    
    return datos

def scrapear_productos_busqueda(url_busqueda, parametro_busqueda, termino_busqueda, cantidad_deseada):
    """Scrapea productos de una búsqueda específica"""
    try:
        # Construir URL de búsqueda
        if '?' in url_busqueda:
            url_final = f"{url_busqueda}&{parametro_busqueda}={termino_busqueda}"
        else:
            url_final = f"{url_busqueda}?{parametro_busqueda}={termino_busqueda}"
        
        print(f"🌐 URL de búsqueda: {url_final}")
        print("⏳ Cargando página de resultados...")
        
        # Configurar headers para simular navegador real
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Realizar request con timeout
        response = requests.get(url_final, headers=headers, timeout=30)
        response.raise_for_status()
        
        print("✅ Respuesta recibida")
        
        # Detectar tipo de respuesta
        print("🔍 Analizando tipo de respuesta...")
        
        # Intentar detectar si es JSON
        try:
            json_data = response.json()
            print("🌐 Detectado: Respuesta JSON")
            return procesar_respuesta_json(json_data, url_busqueda, cantidad_deseada)
        except (ValueError, json.JSONDecodeError):
            print("🌐 Detectado: Respuesta HTML")
            return procesar_respuesta_html(response.text, url_busqueda, cantidad_deseada)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return []
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return []

def procesar_respuesta_json(json_data, url_base, cantidad_deseada):
    """Procesa respuesta JSON de forma universal"""
    try:
        print(f"📦 Procesando JSON con {len(str(json_data))} caracteres")
        
        productos = []
        
        # Buscar productos en diferentes estructuras JSON comunes
        estructuras_posibles = [
            # MercadoLibre
            ('results', 'title', 'price', 'permalink'),
            # Otros sitios
            ('products', 'name', 'price', 'url'),
            ('items', 'title', 'price', 'link'),
            ('data', 'name', 'price', 'url'),
            ('results', 'name', 'price', 'url'),
            ('products', 'title', 'price', 'permalink'),
            ('items', 'name', 'price', 'url'),
            ('search_results', 'title', 'price', 'url'),
            ('listings', 'title', 'price', 'url')
        ]
        
        for estructura in estructuras_posibles:
            lista_key, nombre_key, precio_key, url_key = estructura
            
            # Buscar la lista de productos
            items = buscar_en_json(json_data, lista_key)
            if items and isinstance(items, list) and len(items) > 0:
                print(f"✅ Encontrada estructura: {lista_key}")
                print(f"📦 Encontrados {len(items)} elementos en JSON")
                
                for item in items:
                    if len(productos) >= cantidad_deseada:
                        break
                    
                    if isinstance(item, dict):
                        nombre = buscar_en_json(item, nombre_key)
                        precio = buscar_en_json(item, precio_key)
                        url = buscar_en_json(item, url_key)
                        
                        if nombre and url:
                            # Limpiar precio
                            if precio:
                                if isinstance(precio, dict):
                                    precio = precio.get('amount', '') or precio.get('value', '') or precio.get('price', '')
                                precio = str(precio)
                            
                            # Construir URL completa si es relativa
                            if url and not url.startswith('http'):
                                url = urljoin(url_base, url)
                            
                            # Extraer marca
                            marca = nombre.split()[0] if nombre else ""
                            
                            productos.append({
                                'nombre': str(nombre),
                                'marca': marca,
                                'precio': precio,
                                'tienda': extraer_nombre_tienda(url_base),
                                'url_producto': url
                            })
                
                if productos:
                    print(f"✅ Extraídos {len(productos)} productos del JSON")
                    return productos
        
        print("⚠️ No se encontraron productos en el JSON")
        return []
        
    except json.JSONDecodeError:
        print("❌ Error al parsear JSON")
        return []
    except Exception as e:
        print(f"❌ Error procesando JSON: {e}")
        return []

def buscar_en_json(data, key):
    """Busca una clave en JSON de forma recursiva"""
    if isinstance(data, dict):
        if key in data:
            return data[key]
        for value in data.values():
            result = buscar_en_json(value, key)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = buscar_en_json(item, key)
            if result is not None:
                return result
    return None

def procesar_respuesta_html(html_text, url_base, cantidad_deseada):
    """Procesa respuesta HTML buscando elementos con precios en CLP"""
    soup = BeautifulSoup(html_text, 'html.parser')
    
    print("🔍 Analizando productos buscando precios en CLP...")
    print("📋 Estrategia: Buscar elementos que contengan precios (solo productos reales tienen precios)")
    
    # BUSCAR ELEMENTOS QUE CONTENGAN PRECIOS
    productos = []
    productos_vistos = set()
    
    # Patrón para detectar precios en CLP
    patron_precio = r'\$\s*[\d,]+(?:\.\d{3})*(?:,\d{2})?|\d+(?:\.\d{3})*(?:,\d{2})?\s*(?:pesos|clp|\$)'
    
    # Buscar TODOS los elementos que contengan texto
    todos_elementos = soup.find_all(['div', 'article', 'li', 'section', 'a', 'span', 'p'])
    
    print(f"📦 Analizando {len(todos_elementos)} elementos en busca de precios...")
    
    for elemento in todos_elementos:
        if len(productos) >= cantidad_deseada:
            break
        
        # Obtener todo el texto del elemento
        texto_completo = elemento.get_text()
        
        # Buscar precio en el texto
        match_precio = re.search(patron_precio, texto_completo, re.IGNORECASE)
        
        if match_precio:
            # Si encontró precio, extraer datos del elemento
            datos = extraer_datos_con_precio(elemento, url_base, match_precio.group())
            
            # Validar que sea un producto real
            if datos['nombre'] and len(datos['nombre']) > 5:
                # Evitar duplicados
                nombre_key = datos['nombre'].lower()[:50]
                if nombre_key not in productos_vistos:
                    productos_vistos.add(nombre_key)
                    productos.append(datos)
                    print(f"✅ Producto con precio: {datos['nombre']} - {datos['precio']}")
    
    print(f"\n📊 Total de productos con precios encontrados: {len(productos)}")
    
    # Si no encontró productos, mostrar debugging
    if len(productos) == 0:
        print("\n⚠️ No se encontraron productos con precios. DEBUG:")
        print("🔍 Buscando cualquier texto que contenga números y símbolos de moneda:")
        for i, elemento in enumerate(todos_elementos[:20]):
            texto = elemento.get_text()
            if re.search(r'\d+.*\$|\$.*\d+|\d+.*pesos', texto, re.IGNORECASE):
                print(f"  {i+1}. Texto con posible precio: {texto[:100]}")
    
    return productos

def extraer_datos_con_precio(elemento, url_base, precio_encontrado):
    """Extrae datos de un elemento que contiene precio"""
    datos = {
        'nombre': '',
        'marca': '',
        'precio': precio_encontrado,
        'tienda': extraer_nombre_tienda(url_base),
        'url_producto': ''
    }
    
    # Buscar enlace en el elemento o en sus padres
    enlace = elemento.find('a', href=True)
    if not enlace:
        # Buscar en el elemento padre
        padre = elemento.parent
        if padre:
            enlace = padre.find('a', href=True)
    
    if enlace:
        datos['nombre'] = limpiar_texto(enlace.get_text())
        href = enlace['href']
        if href.startswith('http'):
            datos['url_producto'] = href
        else:
            datos['url_producto'] = urljoin(url_base, href)
    else:
        # Si no hay enlace, usar el texto del elemento como nombre
        texto_completo = elemento.get_text()
        # Remover el precio del texto para obtener el nombre
        nombre_sin_precio = re.sub(patron_precio, '', texto_completo, flags=re.IGNORECASE)
        datos['nombre'] = limpiar_texto(nombre_sin_precio)
    
    # Extraer marca del nombre (primera palabra)
    if datos['nombre']:
        palabras = datos['nombre'].split()
        if palabras:
            datos['marca'] = palabras[0]
    
    return datos

# ========== FUNCIONES DE SCRAPING ESPECÍFICAS ==========

def obtener_o_crear_tienda_por_url(url_producto):
    """Obtiene o crea una tienda basada en la URL del producto"""
    if not url_producto:
        return None, None
    
    # Detectar tienda por URL
    tienda_nombre = None
    tienda_url = None
    tienda_direccion = None
    
    if 'yapo.cl' in url_producto:
        tienda_nombre = 'Yapo'
        tienda_url = 'https://www.yapo.cl'
        tienda_direccion = 'Santiago, Chile'
    elif 'mercadolibre.cl' in url_producto:
        tienda_nombre = 'MercadoLibre'
        tienda_url = 'https://listado.mercadolibre.cl'
        tienda_direccion = 'Buenos Aires, Argentina'
    elif 'paris.cl' in url_producto:
        tienda_nombre = 'Paris'
        tienda_url = 'https://www.paris.cl'
        tienda_direccion = 'Santiago, Chile'
    elif 'falabella.com' in url_producto:
        tienda_nombre = 'Falabella'
        tienda_url = 'https://www.falabella.com'
        tienda_direccion = 'Santiago, Chile'
    else:
        # Extraer dominio como nombre de tienda
        from urllib.parse import urlparse
        dominio = urlparse(url_producto).netloc
        tienda_nombre = dominio.replace('www.', '').split('.')[0].title()
        tienda_url = url_producto
        tienda_direccion = 'Dirección no especificada'
    
    if not tienda_nombre:
        return None, None
    
    # Buscar tienda existente o crear nueva
    try:
        from sqlalchemy.orm import sessionmaker
        from models import Tienda
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        tienda_existente = session.query(Tienda).filter(
            Tienda.nombre == tienda_nombre
        ).first()
        
        if tienda_existente:
            return tienda_existente.id_tienda, tienda_direccion
        else:
            # Crear nueva tienda
            nueva_tienda = Tienda(
                nombre=tienda_nombre,
                direccion=tienda_direccion,
                url=tienda_url,
                id_direccion=None
            )
            session.add(nueva_tienda)
            session.commit()
            session.refresh(nueva_tienda)
            return nueva_tienda.id_tienda, tienda_direccion
            
    except Exception as e:
        print(f"Error al obtener/crear tienda: {e}")
        return None, None

def scrapear_yapo(termino, cantidad):
    import re
    url = f"https://www.yapo.cl/autos-usados?q={termino}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    anuncios = soup.find_all('a', class_='d3-ad-tile__description')
    resultados = []
    for anuncio in anuncios:
        if len(resultados) >= cantidad:
            break
        # Título y marca
        titulo_elem = anuncio.find('span', class_='d3-ad-tile__title')
        titulo = titulo_elem.text.strip() if titulo_elem else ''
        marca = titulo.split()[0] if titulo else ''
        # Precio
        precio_elem = anuncio.find('div', class_='d3-ad-tile__price')
        precio_texto = precio_elem.text.strip() if precio_elem else ''
        precio = limpiar_precio(precio_texto)
        # Descuento
        descuento_elem = anuncio.find('span', class_='d3-ad-tile__price-reduction')
        descuento = limpiar_descuento(descuento_elem.text.strip()) if descuento_elem else None
        # Urgente
        urgente_elem = anuncio.find('div', class_='d3-ad-tile__hallmark')
        urgente = urgente_elem.text.strip() if urgente_elem else ''
        # Vendedor
        vendedor_elem = anuncio.find('div', class_='d3-ad-tile__seller')
        vendedor = vendedor_elem.find('span').text.strip() if vendedor_elem and vendedor_elem.find('span') else ''
        # Ubicación
        ubicacion_elem = anuncio.find('div', class_='d3-ad-tile__location')
        # Extraer solo la comuna/ciudad (primer fragmento antes de salto de línea o después del ícono)
        if ubicacion_elem:
            ubicacion_texto = ubicacion_elem.get_text(strip=True)
            ubicacion = ubicacion_texto.split('\n')[0].strip()
            # Si hay un ícono, puede haber espacios, tomar solo la parte después del ícono
            if ' ' in ubicacion:
                ubicacion = ubicacion.split(' ', 1)[-1].strip()
        else:
            ubicacion = 'No disponible'
        # Descripción
        descripcion_elem = anuncio.find('div', class_='d3-ad-tile__short-description')
        descripcion = descripcion_elem.text.strip() if descripcion_elem else ''
        # Año, combustible, transmisión, kilometraje
        detalles = anuncio.find_all('li', class_='d3-ad-tile__details-item')
        anio = combustible = transmision = kilometraje = ''
        if len(detalles) >= 4:
            anio = detalles[0].text.strip()
            combustible = detalles[1].text.strip()
            transmision = detalles[2].text.strip()
            kilometraje = detalles[3].text.strip()
            kilometraje = re.sub(r'[^\d]', '', kilometraje)  # Solo números
        # URL del producto
        url_producto = anuncio['href'] if anuncio.has_attr('href') else ''
        if url_producto and not url_producto.startswith('http'):
            url_producto = 'https://www.yapo.cl' + url_producto
        # Tienda y dirección
        tienda_nombre = 'Yapo'
        tienda_url = 'https://www.yapo.cl'
        tienda_direccion = ubicacion
        # Diccionario de producto completo
        resultados.append({
            'nombre': titulo,
            'marca': marca,
            'precio': precio,
            'descuento': descuento,
            'preciofinal': precio,  # Asumimos precio final igual al precio si no hay descuento
            'url_producto': url_producto,
            'vendedor': vendedor,
            'urgente': urgente,
            'anio': anio,
            'combustible': combustible,
            'transmision': transmision,
            'kilometraje': kilometraje,
            'descripcion': descripcion,
            'id_tienda': 1,  # Asumimos 1 para Yapo
            'nombre_tienda': tienda_nombre,
            'direccion_tienda': tienda_direccion,
            'url_tienda': tienda_url
        })
    return resultados

def scrapear_mercadolibre(termino, cantidad):
    url = f"https://listado.mercadolibre.cl/{termino}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    html = BeautifulSoup(response.text, 'html.parser')
    productos = html.find_all('div', class_="poly-card poly-card--list poly-card--large poly-card--CORE")
    resultados = []
    for producto in productos:
        if len(resultados) >= cantidad:
            break
        # Nombre y enlace
        nombre_elem = producto.find('a', class_='poly-component__title')
        nombre = nombre_elem.get_text(strip=True) if nombre_elem else ''
        url_producto = nombre_elem['href'] if nombre_elem and nombre_elem.has_attr('href') else ''
        # Marca
        marca_elem = producto.find('span', class_='poly-component__seller')
        marca = ''
        if marca_elem:
            marca_text = marca_elem.get_text(strip=True)
            if marca_text.lower().startswith('por '):
                marca = marca_text[4:].strip()
            else:
                marca = marca_text.strip()
        # Precio actual
        preciofinal = ''
        precio_elem = producto.find('div', class_='poly-price__current')
        if precio_elem:
            precio_span = precio_elem.find('span', class_='andes-money-amount__fraction')
            preciofinal = precio_span.get_text(strip=True) if precio_span else ''
        
        # Convertir precio a decimal
        precio_decimal = limpiar_precio(preciofinal)
        
        # Descuento
        descuento_elem = producto.find('span', class_='andes-money-amount__discount')
        descuento_texto = descuento_elem.get_text(strip=True) if descuento_elem else None
        descuento_decimal = limpiar_descuento(descuento_texto) if descuento_texto else None
        
        # Obtener id_tienda y dirección
        id_tienda, direccion_tienda = obtener_o_crear_tienda_por_url(url_producto)
        
        resultados.append({
            'nombre': nombre,
            'marca': marca,
            'precio': precio_decimal,
            'descuento': descuento_decimal,
            'preciofinal': precio_decimal,
            'url_producto': url_producto,
            'id_tienda': id_tienda,
            'direccion_tienda': direccion_tienda
        })
    return resultados

def scrapear_paris(termino, cantidad):
    url = f"https://www.paris.cl/search/?q={termino}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    html = BeautifulSoup(response.text, 'html.parser')
    productos = html.select('div[role="gridcell"].h-full')
    resultados = []
    for producto in productos:
        if len(resultados) >= cantidad:
            break
        # Marca
        marca_elem = producto.select_one('span.ui-font-semibold')
        marca = marca_elem.text.strip() if marca_elem else ''
        # Nombre (el segundo span.ui-line-clamp-2)
        nombre_elem = producto.select('span.ui-line-clamp-2')
        nombre = nombre_elem[1].text.strip() if nombre_elem and len(nombre_elem) > 1 else (nombre_elem[0].text.strip() if nombre_elem else '')
        # Precio: buscar cualquier <span> que contenga un $ y números
        precio_elem = None
        for span in producto.find_all('span'):
            texto = span.get_text()
            if '$' in texto and any(char.isdigit() for char in texto):
                precio_elem = span
                break
        precio_texto = precio_elem.text.strip() if precio_elem else ''
        
        # Convertir precio a decimal
        precio_decimal = limpiar_precio(precio_texto)
        
        # Descuento (buscar badge de porcentaje)
        descuento_elem = producto.find('div', attrs={'data-testid': 'paris-label'})
        descuento_texto = descuento_elem.get_text(strip=True) if descuento_elem else None
        descuento_decimal = limpiar_descuento(descuento_texto) if descuento_texto else None
        
        # Enlace
        enlace = producto.find('a', href=True)
        url_producto = enlace['href'] if enlace else ''
        if url_producto and not url_producto.startswith('http'):
            url_producto = 'https://www.paris.cl' + url_producto
        
        # Obtener id_tienda y dirección
        id_tienda, direccion_tienda = obtener_o_crear_tienda_por_url(url_producto)
        
        resultados.append({
            'nombre': nombre,
            'marca': marca,
            'precio': precio_decimal,
            'descuento': descuento_decimal,
            'preciofinal': precio_decimal,
            'url_producto': url_producto,
            'id_tienda': id_tienda,
            'direccion_tienda': direccion_tienda
        })
    return resultados

def scrapear_falabella(termino, cantidad):
    url = f"https://www.falabella.com/falabella-cl/search?Ntt={termino}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers)
    html = BeautifulSoup(response.text, 'html.parser')
    
    # Buscar productos en Falabella (basado en la estructura HTML proporcionada)
    productos = html.find_all('div', class_='jsx-2858414180')
    resultados = []
    
    for producto in productos:
        if len(resultados) >= cantidad:
            break
            
        try:
            # Buscar nombre del producto
            nombre_elem = producto.find('span', class_='copy10')
            nombre = nombre_elem.text.strip() if nombre_elem else ''
            
            # Buscar precio actual (el primer precio en la lista)
            precio_elem = producto.find('li', class_='prices-0')
            if precio_elem:
                precio_span = precio_elem.find('span', class_='copy10')
                precio_texto = precio_span.text.strip() if precio_span else ''
            else:
                precio_texto = ''
            
            # Buscar precio normal (precio tachado)
            precio_normal_elem = producto.find('li', class_='prices-1')
            if precio_normal_elem:
                precio_normal_span = precio_normal_elem.find('span', class_='copy3')
                precio_normal_texto = precio_normal_span.text.strip() if precio_normal_span else ''
            else:
                precio_normal_texto = ''
            
            # Convertir precios a decimal
            precio_decimal = limpiar_precio(precio_texto)
            precio_normal_decimal = limpiar_precio(precio_normal_texto)
            
            # Buscar descuento
            descuento_elem = producto.find('span', class_='discount-badge-item')
            descuento_texto = descuento_elem.text.strip() if descuento_elem else None
            descuento_decimal = limpiar_descuento(descuento_texto) if descuento_texto else None
            
            # Buscar enlace del producto
            enlace = producto.find('a', href=True)
            url_producto = enlace['href'] if enlace else ''
            if url_producto and not url_producto.startswith('http'):
                url_producto = 'https://www.falabella.com' + url_producto
            
            # Extraer marca del nombre (primera palabra)
            marca = nombre.split()[0] if nombre else ''
            
            # Precio final (usar precio actual si existe, sino precio normal)
            preciofinal = precio_decimal if precio_decimal else precio_normal_decimal
            
            # Obtener id_tienda y dirección
            id_tienda, direccion_tienda = obtener_o_crear_tienda_por_url(url_producto)
            
            if nombre and (precio_decimal or precio_normal_decimal):  # Solo agregar si tiene nombre y precio
                resultados.append({
                    'nombre': nombre,
                    'marca': marca,
                    'precio': precio_normal_decimal,  # Precio original
                    'descuento': descuento_decimal,
                    'preciofinal': preciofinal,  # Precio final (con descuento)
                    'url_producto': url_producto,
                    'id_tienda': id_tienda,
                    'direccion_tienda': direccion_tienda
                })
                
        except Exception as e:
            continue  # Si hay error con un producto, continuar con el siguiente
    
    return resultados

# ========== FUNCIONES AUXILIARES ==========

def limpiar_precio(precio_texto):
    """Convierte texto de precio a decimal"""
    if not precio_texto:
        return None
    
    # Remover símbolos de moneda y espacios
    precio_limpio = precio_texto.replace('$', '').replace(' ', '').replace('.', '').replace(',', '.')
    
    try:
        # Convertir a float y luego a Decimal para precisión
        from decimal import Decimal
        return float(precio_limpio)
    except (ValueError, TypeError):
        return None

def limpiar_descuento(descuento_texto):
    """Convierte texto de descuento a decimal"""
    if not descuento_texto:
        return None
    
    # Remover símbolos de porcentaje y espacios
    descuento_limpio = descuento_texto.replace('%', '').replace('-', '').replace(' ', '')
    
    try:
        # Convertir a float
        return float(descuento_limpio)
    except (ValueError, TypeError):
        return None

# ========== DETECCIÓN DE TIENDA ==========

def detectar_tienda(url):
    if 'yapo.cl' in url:
        return 'yapo'
    elif 'mercadolibre.cl' in url:
        return 'mercadolibre'
    elif 'paris.cl' in url:
        return 'paris'
    elif 'falabella.com' in url:
        return 'falabella'
    else:
        return None

# ========== GUARDADO DE RESULTADOS ==========

def guardar_resultados(resultados, columnas, nombre_archivo):
    carpeta = 'archivos'
    os.makedirs(carpeta, exist_ok=True)
    ruta_csv = os.path.join(carpeta, nombre_archivo + '.csv')
    ruta_excel = os.path.join(carpeta, nombre_archivo + '.xlsx')
    with open(ruta_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for row in resultados:
            writer.writerow(row)
    df = pd.DataFrame(resultados)
    df.to_excel(ruta_excel, index=False)
    print(f"Archivos '{ruta_csv}' y '{ruta_excel}' generados correctamente.")

# ========== INTERFAZ PRINCIPAL ==========

def main():
    print("\n==================================================")
    print("🗷  SCRAPER MULTITIENDAS")
    print("==================================================")
    url = seleccionar_tienda()
    print(f"\n✅ URL seleccionada: {url}")
    termino = input("\n🔍 ¿Qué quieres buscar?: ").strip()
    if not termino:
        print("❌ Término de búsqueda no válido.")
        return
    try:
        cantidad = int(input("📊 ¿Cuántos productos quieres obtener?: ").strip())
        if cantidad <= 0:
            print("❌ La cantidad debe ser mayor a 0.")
            return
    except ValueError:
        print("❌ Cantidad no válida. Debe ser un número.")
        return
    nombre_archivo = input("💾 Nombre del archivo (sin extensión): ").strip()
    if not nombre_archivo:
        print("❌ Nombre de archivo no válido.")
        return
    print(f"\n🔄 Iniciando scraping...")
    print(f"   URL: {url}")
    print(f"   Búsqueda: '{termino}'")
    print(f"   Cantidad: {cantidad} productos")
    print(f"   Archivo: {nombre_archivo}")
    print("-" * 50)
    tienda = detectar_tienda(url)
    resultados = []
    try:
        if tienda == 'yapo':
            resultados = scrapear_yapo(termino, cantidad)
        elif tienda == 'mercadolibre':
            resultados = scrapear_mercadolibre(termino, cantidad)
        elif tienda == 'paris':
            resultados = scrapear_paris(termino, cantidad)
        elif tienda == 'falabella':
            resultados = scrapear_falabella(termino, cantidad)
        else:
            print(f"❌ Tienda no soportada para la URL: {url}")
            return
        if resultados:
            columnas = [
                'nombre', 'marca', 'precio', 'descuento', 'preciofinal', 'url_producto',
                'vendedor', 'urgente', 'anio', 'combustible', 'transmision', 'kilometraje',
                'descripcion', 'id_tienda', 'nombre_tienda', 'direccion_tienda', 'url_tienda'
            ]
            guardar_resultados(resultados, columnas, nombre_archivo)
            print(f"\n✅ Scraping completado exitosamente!")
            print(f"📊 Productos encontrados: {len(resultados)}")
        else:
            print("❌ No se encontraron productos.")
    except Exception as e:
        print(f"❌ Error durante el scraping: {e}")
        print("💡 Sugerencias:")
        print("   - Verifica tu conexión a internet")
        print("   - Intenta con un término de búsqueda diferente")
        print("   - La tienda puede haber cambiado su estructura")

if __name__ == "__main__":
    main()
