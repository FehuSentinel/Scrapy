import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
from dotenv import load_dotenv
import sys
from decimal import Decimal

# Cargar variables de entorno (intenta .env primero, luego config.env)
load_dotenv('.env')  # Intenta cargar .env
load_dotenv('config.env', override=True)  # Sobrescribe con config.env si existe

# Conexión PostgreSQL usando variables de entorno
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'tu_contraseña')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'alquimia')

DATABASE_URL = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def mostrar_menu_archivos(archivos_csv):
    """Muestra el menú de archivos disponibles"""
    print("\n" + "="*50)
    print("    📁 ARCHIVOS CSV DISPONIBLES")
    print("="*50)
    for i, archivo in enumerate(archivos_csv, 1):
        ruta_completa = os.path.join('archivos', archivo)
        tamaño = os.path.getsize(ruta_completa)
        print(f"{i}. {archivo} ({tamaño:,} bytes)")
    print("0. 🔙 Volver atrás")
    print("="*50)

def mostrar_menu_tablas(tablas_disponibles):
    """Muestra el menú de tablas disponibles"""
    print("\n" + "="*50)
    print("    🗄️ TABLAS DISPONIBLES")
    print("="*50)
    for i, nombre_tabla in enumerate(tablas_disponibles.keys(), 1):
        print(f"{i}. {nombre_tabla}")
    print(f"{len(tablas_disponibles) + 1}. 📊 Subir archivo completo (todas las tablas)")
    print("0. 🔙 Volver atrás")
    print("="*50)

def procesar_archivo_completo(df, archivo_elegido):
    """Procesa un archivo completo con todas las tablas"""
    print(f"\n🚀 PROCESANDO ARCHIVO COMPLETO: {archivo_elegido}")
    print("="*60)
    
    # Verificar que el archivo tenga las columnas necesarias para todas las tablas
    columnas_requeridas = [
        'id_usuario', 'nombre_usuario', 'apellido_usuario', 'email_usuario', 'edad_usuario', 'sexo_usuario',
        'id_tienda', 'nombre_tienda', 'direccion_tienda', 'url_tienda',
        'id_producto', 'nombre_producto', 'marca_producto', 'precio_producto', 'url_producto', 'promocion_producto', 'precio_final_producto',
        'id_promocion', 'tipo_promocion', 'fecha_inicio_promocion', 'fecha_fin_promocion',
        'id_tiempo', 'fecha_venta', 'dia_venta', 'mes_venta', 'año_venta', 'trimestre_venta', 'festivo_venta',
        'id_venta', 'cantidad_vendida', 'precio_unitario', 'descuento_unitario', 'precio_final_unitario', 'total_bruto', 'total_descuento', 'total_neto'
    ]
    
    faltantes = [col for col in columnas_requeridas if col not in df.columns]
    if faltantes:
        print(f"❌ [ERROR] El archivo no es un archivo completo. Faltan columnas:")
        for col in faltantes[:10]:  # Mostrar solo las primeras 10
            print(f"   - {col}")
        if len(faltantes) > 10:
            print(f"   ... y {len(faltantes) - 10} más")
        print("\n💡 Este archivo debe ser generado por el Scraper Integrado (Opción 3)")
        return False
    
    print("✅ Archivo completo detectado. Procesando todas las tablas...")
    
    try:
        # 1. Procesar USUARIOS
        print(f"\n👥 Procesando USUARIOS...")
        usuarios_df = df[['id_usuario', 'nombre_usuario', 'apellido_usuario', 'email_usuario', 'edad_usuario', 'sexo_usuario']].drop_duplicates()
        usuarios_df.columns = ['id_usuario', 'nombre', 'apellido', 'email', 'edad', 'sexo']
        usuarios_df.to_sql('usuarios', engine, if_exists='append', index=False)
        print(f"   ✅ {len(usuarios_df)} usuarios cargados")
        
        # 2. Procesar TIENDAS (PRIMERO para evitar problemas de FK)
        print(f"\n🏪 Procesando TIENDAS...")
        tiendas_df = df[['id_tienda', 'nombre_tienda', 'direccion_tienda', 'url_tienda']].drop_duplicates()
        tiendas_df.columns = ['id_tienda', 'nombre', 'direccion', 'url']
        tiendas_df.to_sql('tienda', engine, if_exists='append', index=False)
        print(f"   ✅ {len(tiendas_df)} tiendas cargadas")
        
        # 3. Procesar PROMOCIONES
        print(f"\n🎯 Procesando PROMOCIONES...")
        promociones_df = df[['id_promocion', 'tipo_promocion', 'fecha_inicio_promocion', 'fecha_fin_promocion']].drop_duplicates()
        promociones_df.columns = ['id_promocion', 'tipo_promocion', 'fecha_inicio', 'fecha_fin']
        # Filtrar solo promociones válidas (id_promocion > 0)
        promociones_df = promociones_df[promociones_df['id_promocion'] > 0]
        if len(promociones_df) > 0:
            promociones_df.to_sql('promocion', engine, if_exists='append', index=False)
            print(f"   ✅ {len(promociones_df)} promociones cargadas")
        else:
            print(f"   ⚠️ No hay promociones válidas para cargar")
        
        # 4. Procesar PRODUCTOS (con manejo de promociones)
        print(f"\n🛍️ Procesando PRODUCTOS...")
        productos_df = df[['id_producto', 'nombre_producto', 'marca_producto', 'precio_producto', 'url_producto', 'promocion_producto', 'precio_final_producto', 'id_tienda']].drop_duplicates()
        productos_df.columns = ['id_producto', 'nombre', 'marca', 'precio', 'url_producto', 'promocion', 'preciofinal', 'id_tienda']
        
        # Manejar promociones: convertir 0 a NULL para evitar problemas de FK
        productos_df['promocion'] = productos_df['promocion'].replace(0, None)
        productos_df['promocion'] = productos_df['promocion'].where(productos_df['promocion'] > 0, None)
        
        productos_df.to_sql('productos', engine, if_exists='append', index=False)
        print(f"   ✅ {len(productos_df)} productos cargados")
        
        # 5. Procesar TIEMPO
        print(f"\n⏰ Procesando TIEMPO...")
        tiempo_df = df[['id_tiempo', 'fecha_venta', 'dia_venta', 'mes_venta', 'año_venta', 'trimestre_venta', 'festivo_venta']].drop_duplicates()
        tiempo_df.columns = ['id_tiempo', 'fecha', 'dia', 'mes', 'año', 'trimestre', 'festivo']
        tiempo_df.to_sql('tiempo', engine, if_exists='append', index=False)
        print(f"   ✅ {len(tiempo_df)} registros de tiempo cargados")
        
        # 6. Procesar VENTAS
        print(f"\n💰 Procesando VENTAS...")
        
        # Verificar qué columnas de ventas están disponibles
        columnas_ventas_disponibles = [
            'id_venta', 'id_usuario', 'id_producto', 'id_tienda', 'id_tiempo', 'id_promocion', 
            'cantidad_vendida', 'precio_unitario', 'descuento_unitario', 'precio_final_unitario', 
            'total_bruto', 'total_descuento', 'total_neto'
        ]
        
        columnas_ventas_existentes = [col for col in columnas_ventas_disponibles if col in df.columns]
        
        print(f"   📋 Columnas de ventas encontradas: {columnas_ventas_existentes}")
        
        # Si falta id_tienda, asignar un valor por defecto
        if 'id_tienda' not in df.columns:
            print(f"   ⚠️ Columna 'id_tienda' no encontrada, asignando valor por defecto (1)")
            ventas_df = df[columnas_ventas_existentes].copy()
            ventas_df['id_tienda'] = 1  # Valor por defecto
        else:
            ventas_df = df[columnas_ventas_existentes].copy()
        
        # Renombrar columnas para coincidir con el modelo
        columnas_finales = ['id_venta', 'id_usuario', 'id_producto', 'id_tienda', 'id_tiempo', 'id_promocion', 'cantidad_vendida', 'precio_unitario', 'descuento_unitario', 'precio_final_unitario', 'total_bruto', 'total_descuento', 'total_neto']
        
        # Asegurar que todas las columnas necesarias estén presentes
        for col in columnas_finales:
            if col not in ventas_df.columns:
                if col == 'id_tienda':
                    ventas_df[col] = 1  # Valor por defecto
                elif col == 'id_promocion':
                    ventas_df[col] = None  # NULL por defecto
                else:
                    ventas_df[col] = 0  # 0 por defecto para otros campos
        
        # Reordenar columnas
        ventas_df = ventas_df[columnas_finales]
        
        # Manejar promociones en ventas: convertir 0 a NULL
        ventas_df['id_promocion'] = ventas_df['id_promocion'].replace(0, None)
        ventas_df['id_promocion'] = ventas_df['id_promocion'].where(ventas_df['id_promocion'] > 0, None)
        
        ventas_df.to_sql('ventas', engine, if_exists='append', index=False)
        print(f"   ✅ {len(ventas_df)} ventas cargadas")
        
        print(f"\n🎉 ¡ARCHIVO COMPLETO PROCESADO EXITOSAMENTE!")
        print(f"📊 Resumen:")
        print(f"   👥 Usuarios: {len(usuarios_df)}")
        print(f"   🏪 Tiendas: {len(tiendas_df)}")
        print(f"   🛍️ Productos: {len(productos_df)}")
        print(f"   🎯 Promociones: {len(promociones_df)}")
        print(f"   ⏰ Tiempo: {len(tiempo_df)}")
        print(f"   💰 Ventas: {len(ventas_df)}")
        
        return True
        
    except Exception as e:
        print(f"❌ [ERROR] Error al procesar archivo completo: {e}")
        print(f"📋 Columnas disponibles en el archivo: {list(df.columns)}")
        return False

def obtener_o_crear_tienda(nombre_tienda):
    """Obtiene una tienda existente o crea una nueva"""
    # Buscar tienda existente
    tienda_existente = session.query(models.Tienda).filter(
        models.Tienda.nombre == nombre_tienda
    ).first()
    
    if tienda_existente:
        print(f"   [EXISTE] Tienda '{nombre_tienda}' ya existe (ID: {tienda_existente.id_tienda})")
        return tienda_existente.id_tienda
    else:
        # Crear nueva tienda
        nueva_tienda = models.Tienda(
            nombre=nombre_tienda,
            direccion=None,
            url=None,
            id_direccion=None
        )
        session.add(nueva_tienda)
        session.commit()
        session.refresh(nueva_tienda)
        print(f"   [NUEVA] Nueva tienda creada: '{nombre_tienda}' (ID: {nueva_tienda.id_tienda})")
        return nueva_tienda.id_tienda

def obtener_o_crear_direccion(direccion_texto):
    """Obtiene una dirección existente o crea una nueva"""
    if not direccion_texto:
        return None
    
    # Buscar dirección existente
    direccion_existente = session.query(models.Direccion).filter(
        models.Direccion.calle == direccion_texto
    ).first()
    
    if direccion_existente:
        print(f"   [EXISTE] Dirección '{direccion_texto}' ya existe (ID: {direccion_existente.id_direccion})")
        return direccion_existente.id_direccion
    else:
        # Parsear la dirección (formato simple: "Ciudad, País")
        partes = direccion_texto.split(', ')
        if len(partes) >= 2:
            ciudad = partes[0]
            region = partes[1]
        else:
            ciudad = direccion_texto
            region = 'No especificada'
        
        # Crear nueva dirección
        nueva_direccion = models.Direccion(
            calle=direccion_texto,
            numero='N/A',
            comuna='N/A',
            ciudad=ciudad,
            region=region
        )
        session.add(nueva_direccion)
        session.commit()
        session.refresh(nueva_direccion)
        print(f"   [NUEVA] Nueva dirección creada: '{direccion_texto}' (ID: {nueva_direccion.id_direccion})")
        return nueva_direccion.id_direccion

def actualizar_tienda_con_direccion(id_tienda, direccion_texto):
    """Actualiza una tienda existente con su dirección"""
    if not id_tienda or not direccion_texto:
        return
    
    try:
        # Obtener la tienda
        tienda = session.query(models.Tienda).filter(
            models.Tienda.id_tienda == id_tienda
        ).first()
        
        if tienda:
            # Obtener o crear la dirección
            id_direccion = obtener_o_crear_direccion(direccion_texto)
            
            # Actualizar la tienda con la dirección
            tienda.direccion = direccion_texto
            tienda.id_direccion = id_direccion
            session.commit()
            print(f"   [ACTUALIZADA] Tienda '{tienda.nombre}' actualizada con dirección")
            
    except Exception as e:
        print(f"   [ERROR] Error al actualizar tienda: {e}")

def verificar_duplicados_productos(df):
    """Verifica si hay productos duplicados en la base de datos"""
    print(f"\n[VERIFICANDO] Verificando duplicados existentes...")
    
    # Obtener productos existentes de la base de datos
    productos_existentes = session.query(models.Producto).all()
    
    # Crear un conjunto de combinaciones únicas existentes (nombre + id_tienda)
    existentes = set()
    for producto in productos_existentes:
        clave = f"{producto.nombre.lower().strip()}_{producto.id_tienda}"
        existentes.add(clave)
    
    # Verificar duplicados en el nuevo archivo
    duplicados = []
    nuevos = []
    
    for idx, row in df.iterrows():
        nombre = str(row['nombre']).lower().strip()
        id_tienda = row.get('id_tienda', None)
        if id_tienda:
            clave = f"{nombre}_{id_tienda}"
        else:
            clave = f"{nombre}_sin_tienda"
        
        if clave in existentes:
            duplicados.append({
                'indice': idx,
                'nombre': row['nombre'],
                'id_tienda': id_tienda,
                'clave': clave
            })
        else:
            nuevos.append(idx)
    
    print(f"   [INFO] Productos en el archivo: {len(df)}")
    print(f"   [NUEVOS] Productos nuevos: {len(nuevos)}")
    print(f"   [DUPLICADOS] Productos duplicados: {len(duplicados)}")
    
    if duplicados:
        print(f"\n[DUPLICADOS] Productos duplicados encontrados:")
        for dup in duplicados[:5]:  # Mostrar solo los primeros 5
            print(f"   - {dup['nombre']} (ID Tienda: {dup['id_tienda']})")
        
        if len(duplicados) > 5:
            print(f"   ... y {len(duplicados) - 5} mas")
        
        print(f"\n¿Qué deseas hacer?")
        print(f"1. [NUEVOS] Cargar solo productos nuevos (omitir duplicados)")
        print(f"2. [SOBRESCRIBIR] Sobrescribir productos duplicados")
        print(f"3. [CANCELAR] Cancelar la carga")
        print(f"0. 🔙 Volver atrás")
        
        while True:
            opcion = input("Selecciona una opción (0-3): ").strip()
            if opcion == "0":
                print("[CANCELADO] Volviendo al menú principal...")
                return None, []
            elif opcion == "1":
                # Filtrar solo productos nuevos
                df_nuevo = df.iloc[nuevos].copy()
                print(f"[OK] Se cargarán {len(df_nuevo)} productos nuevos")
                return df_nuevo, duplicados
            elif opcion == "2":
                print(f"[ADVERTENCIA] Se sobrescribirán {len(duplicados)} productos duplicados")
                return df, duplicados
            elif opcion == "3":
                print("[CANCELADO] Carga cancelada")
                return None, []
            else:
                print("[ERROR] Opción inválida. Selecciona 0, 1, 2 o 3.")
    
    return df, []

def procesar_productos(df, nombre_tabla):
    """Procesa productos para el nuevo modelo"""
    print(f"\n[PROCESANDO] Procesando productos...")
    
    # Verificar duplicados primero
    resultado = verificar_duplicados_productos(df)
    if resultado[0] is None:
        return False
    
    df, duplicados = resultado
    
    if len(df) == 0:
        print("   [ERROR] No hay productos nuevos para cargar")
        return False
    
    # Si hay duplicados y el usuario eligió sobrescribir, eliminar duplicados existentes
    if duplicados and len(duplicados) > 0:
        print(f"   [ELIMINANDO] Eliminando {len(duplicados)} productos duplicados existentes...")
        for dup in duplicados:
            session.query(models.Producto).filter(
                models.Producto.nombre == dup['nombre'],
                models.Producto.id_tienda == dup['id_tienda']
            ).delete()
        session.commit()
        print(f"   [OK] Productos duplicados eliminados")
    
    # Procesar direcciones de tiendas si están disponibles
    if 'direccion_tienda' in df.columns:
        print(f"   [PROCESANDO] Procesando direcciones de tiendas...")
        for idx, row in df.iterrows():
            if pd.notna(row['id_tienda']) and pd.notna(row['direccion_tienda']):
                actualizar_tienda_con_direccion(row['id_tienda'], row['direccion_tienda'])
    
    # Preparar datos para inserción
    columnas_modelo = [col.name for col in models.Producto.__table__.columns]
    columnas_modelo_sin_id = columnas_modelo[1:]  # Excluir id_producto
    
    # Seleccionar solo las columnas que existen en el modelo (excluir direccion_tienda)
    columnas_disponibles = [col for col in columnas_modelo_sin_id if col in df.columns and col != 'direccion_tienda']
    df_final = df[columnas_disponibles].copy()
    
    # Convertir columnas numéricas
    if 'precio' in df_final.columns:
        df_final['precio'] = pd.to_numeric(df_final['precio'], errors='coerce')
    if 'descuento' in df_final.columns:
        df_final['descuento'] = pd.to_numeric(df_final['descuento'], errors='coerce')
    if 'preciofinal' in df_final.columns:
        df_final['preciofinal'] = pd.to_numeric(df_final['preciofinal'], errors='coerce')
    
    # Insertar productos
    df_final.to_sql(nombre_tabla, engine, if_exists='append', index=False)
    
    print(f"   [OK] {len(df_final)} productos cargados exitosamente")
    return True

def procesar_usuarios(df, nombre_tabla):
    """Procesa usuarios para el nuevo modelo"""
    print(f"\n[PROCESANDO] Procesando usuarios...")
    
    # Preparar datos para inserción
    columnas_modelo = [col.name for col in models.Usuario.__table__.columns]
    columnas_modelo_sin_id = columnas_modelo[1:]  # Excluir id_usuario
    
    # Seleccionar solo las columnas que existen en el modelo
    columnas_disponibles = [col for col in columnas_modelo_sin_id if col in df.columns]
    df_final = df[columnas_disponibles].copy()
    
    # Insertar usuarios
    df_final.to_sql(nombre_tabla, engine, if_exists='append', index=False)
    
    print(f"   [OK] {len(df_final)} usuarios cargados exitosamente")
    return True

def procesar_tiendas(df, nombre_tabla):
    """Procesa tiendas para el nuevo modelo"""
    print(f"\n[PROCESANDO] Procesando tiendas...")
    
    # Preparar datos para inserción
    columnas_modelo = [col.name for col in models.Tienda.__table__.columns]
    columnas_modelo_sin_id = columnas_modelo[1:]  # Excluir id_tienda
    
    # Seleccionar solo las columnas que existen en el modelo
    columnas_disponibles = [col for col in columnas_modelo_sin_id if col in df.columns]
    df_final = df[columnas_disponibles].copy()
    
    # Insertar tiendas
    df_final.to_sql(nombre_tabla, engine, if_exists='append', index=False)
    
    print(f"   [OK] {len(df_final)} tiendas cargadas exitosamente")
    return True

def main():
    """Función principal del programa"""
    print("🚀 CARGADOR DE ARCHIVOS CSV A BASE DE DATOS")
    print("="*50)
    
    # Verificar que existe la carpeta archivos
    carpeta = 'archivos'
    if not os.path.exists(carpeta):
        print(f"❌ [ERROR] La carpeta '{carpeta}' no existe.")
        print("💡 Ejecuta primero el Scraper Integrado (Opción 3) para generar archivos.")
        return
    
    # Listar archivos CSV
    archivos_csv = [f for f in os.listdir(carpeta) if f.endswith('.csv')]
    
    if not archivos_csv:
        print(f"❌ [ERROR] No hay archivos CSV en la carpeta '{carpeta}'.")
        print("💡 Ejecuta primero el Scraper Integrado (Opción 3) para generar archivos.")
        return
    
    # Menú de archivos
    while True:
        mostrar_menu_archivos(archivos_csv)
        op_archivo = input("Selecciona el número del archivo que deseas subir: ").strip()
        
        if op_archivo == "0":
            print("👋 ¡Volviendo al menú principal!")
            return
        
        if not op_archivo.isdigit() or int(op_archivo) < 1 or int(op_archivo) > len(archivos_csv):
            print("❌ [ERROR] Opción inválida.")
            continue
        
        archivo_elegido = archivos_csv[int(op_archivo) - 1]
        ruta_csv = os.path.join(carpeta, archivo_elegido)
        
        # Leer CSV
        try:
            df = pd.read_csv(ruta_csv)
            df.columns = df.columns.str.strip().str.lower()
        except Exception as e:
            print(f"❌ [ERROR] No se pudo leer el archivo: {e}")
            continue
        
        print(f"\n📄 [ARCHIVO] Archivo: {archivo_elegido}")
        print(f"📊 [INFO] Filas: {len(df)}")
        print(f"📋 [INFO] Columnas: {list(df.columns)}")
        
        # Listar tablas disponibles desde models.py
        tablas_disponibles = {}
        for nombre_clase in dir(models):
            objeto = getattr(models, nombre_clase)
            if hasattr(objeto, '__tablename__'):
                tablas_disponibles[objeto.__tablename__] = objeto
        
        if not tablas_disponibles:
            print("❌ [ERROR] No hay tablas definidas en models.py")
            return
        
        # Menú de tablas
        while True:
            mostrar_menu_tablas(tablas_disponibles)
            op_tabla = input("¿A qué tabla deseas subir los datos? (elige número): ").strip()
            
            if op_tabla == "0":
                print("🔙 Volviendo a selección de archivo...")
                break
            
            if not op_tabla.isdigit() or int(op_tabla) < 1 or int(op_tabla) > len(tablas_disponibles) + 1:
                print("❌ [ERROR] Opción inválida.")
                continue
            
            # Procesar según la opción seleccionada
            if int(op_tabla) == len(tablas_disponibles) + 1:
                # Opción: Subir archivo completo
                if procesar_archivo_completo(df, archivo_elegido):
                    print(f"\n✅ [OK] '{archivo_elegido}' fue procesado completamente.")
                else:
                    print(f"\n❌ [ERROR] Error al procesar '{archivo_elegido}' como archivo completo.")
                break
            else:
                # Opción: Subir a tabla específica
                nombre_tabla = list(tablas_disponibles.keys())[int(op_tabla) - 1]
                clase_modelo = tablas_disponibles[nombre_tabla]
                
                # Procesar según el tipo de tabla
                if nombre_tabla == 'productos':
                    # Verificar columnas requeridas para productos
                    columnas_requeridas = ['nombre']
                    faltantes = [col for col in columnas_requeridas if col not in df.columns]
                    if faltantes:
                        print("❌ [ERROR] Faltan columnas requeridas:", faltantes)
                        print("💡 [AYUDA] El archivo debe contener al menos: nombre")
                        continue
                    
                    # Procesar productos
                    if procesar_productos(df, nombre_tabla):
                        print(f"✅ [OK] '{archivo_elegido}' fue cargado correctamente a la tabla '{nombre_tabla}'.")
                    else:
                        print(f"❌ [ERROR] Error al cargar '{archivo_elegido}' a la tabla '{nombre_tabla}'.")
                    break

                elif nombre_tabla == 'usuarios':
                    # Verificar columnas requeridas para usuarios
                    columnas_requeridas = ['nombre', 'apellido', 'email']
                    faltantes = [col for col in columnas_requeridas if col not in df.columns]
                    if faltantes:
                        print("❌ [ERROR] Faltan columnas requeridas:", faltantes)
                        print("💡 [AYUDA] El archivo debe contener: nombre, apellido, email")
                        continue
                    
                    # Procesar usuarios
                    if procesar_usuarios(df, nombre_tabla):
                        print(f"✅ [OK] '{archivo_elegido}' fue cargado correctamente a la tabla '{nombre_tabla}'.")
                    else:
                        print(f"❌ [ERROR] Error al cargar '{archivo_elegido}' a la tabla '{nombre_tabla}'.")
                    break

                elif nombre_tabla == 'tienda':
                    # Verificar columnas requeridas para tiendas
                    columnas_requeridas = ['nombre']
                    faltantes = [col for col in columnas_requeridas if col not in df.columns]
                    if faltantes:
                        print("❌ [ERROR] Faltan columnas requeridas:", faltantes)
                        print("💡 [AYUDA] El archivo debe contener al menos: nombre")
                        continue
                    
                    # Procesar tiendas
                    if procesar_tiendas(df, nombre_tabla):
                        print(f"✅ [OK] '{archivo_elegido}' fue cargado correctamente a la tabla '{nombre_tabla}'.")
                    else:
                        print(f"❌ [ERROR] Error al cargar '{archivo_elegido}' a la tabla '{nombre_tabla}'.")
                    break

                else:
                    # Para otras tablas, usar el proceso genérico
                    # Obtener columnas del modelo
                    columnas_modelo = [col.name for col in clase_modelo.__table__.columns]
                    columna_id = columnas_modelo[0]  # asumimos la primera es la PK
                    columnas_modelo_sin_id = columnas_modelo[1:]
                    columnas_modelo_lower = [c.lower() for c in columnas_modelo_sin_id]

                    # Validar campos requeridos
                    faltantes = [col for col in columnas_modelo_lower if col not in df.columns]
                    if faltantes:
                        print("❌ [ERROR] Faltan columnas requeridas:", faltantes)
                        print("💡 [AYUDA] Asegúrate de que tu archivo CSV contenga todas las columnas necesarias.")
                        continue

                    # Renombrar columnas para coincidir con modelo real (respetando mayúsculas)
                    renombres = {}
                    for col_modelo in columnas_modelo_sin_id:
                        col_csv = col_modelo.lower()
                        if col_csv in df.columns:
                            renombres[col_csv] = col_modelo

                    df.rename(columns=renombres, inplace=True)

                    # Subir a tabla
                    df = df[renombres.values()]  # reordenar columnas si es necesario
                    df.to_sql(nombre_tabla, engine, if_exists='append', index=False)

                    print(f"✅ [OK] '{archivo_elegido}' fue cargado correctamente a la tabla '{nombre_tabla}'.")
                    break
        
        # Preguntar si quiere continuar con otro archivo
        continuar = input("\n¿Deseas cargar otro archivo? (s/n): ").strip().lower()
        if continuar not in ['s', 'si', 'sí', 'y', 'yes']:
            print("👋 ¡Hasta luego!")
            break

if __name__ == "__main__":
    main()
