import os
from sqlalchemy import create_engine, text
import models
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('.env')
load_dotenv('config.env', override=True)

# Conexión PostgreSQL
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'tu_contraseña')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'alquimia')

DATABASE_URL = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(DATABASE_URL)

def mostrar_menu_principal():
    """Muestra el menú principal del consultor SQL"""
    print("\n" + "="*60)
    print("    🗄️  CONSULTOR SQL - BASE DE DATOS")
    print("="*60)
    print("1. 📊 Ver todas las tablas")
    print("2. 🔍 Consultas SQL personalizadas")
    print("3. 📈 Consultas predefinidas (ejemplos)")
    print("4. 🛍️ Ver productos con promociones")
    print("5. 💰 Ver ventas y hechos")
    print("6. 👥 Ver usuarios y sus compras")
    print("0. 🚪 Volver al menú principal")
    print("="*60)

def ver_todas_las_tablas():
    """Muestra todas las tablas disponibles con información básica"""
    print("\n📊 TABLAS DISPONIBLES EN LA BASE DE DATOS")
    print("="*60)
    
    try:
        with engine.connect() as conn:
            # Obtener lista de tablas
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tablas = [row[0] for row in result]
            
            if not tablas:
                print("❌ No hay tablas en la base de datos")
                return
            
            print(f"📋 Total de tablas: {len(tablas)}")
            print("-" * 60)
            
            for i, tabla in enumerate(tablas, 1):
                # Contar registros en cada tabla
                result = conn.execute(text(f"SELECT COUNT(*) FROM {tabla}"))
                count = result.scalar()
                
                # Obtener estructura básica
                result = conn.execute(text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{tabla}' 
                    ORDER BY ordinal_position 
                    LIMIT 3;
                """))
                
                columnas = [f"{row[0]}({row[1]})" for row in result]
                columnas_str = ", ".join(columnas)
                if len(columnas) == 3:
                    columnas_str += "..."
                
                print(f"{i:2d}. {tabla:<15} | Registros: {count:>6} | Columnas: {columnas_str}")
            
            print("-" * 60)
            
    except Exception as e:
        print(f"❌ Error al consultar las tablas: {e}")

def consulta_sql_personalizada():
    """Permite al usuario ejecutar consultas SQL personalizadas"""
    print("\n🔍 CONSULTA SQL PERSONALIZADA")
    print("="*60)
    print("💡 Escribe tu consulta SQL. Ejemplos:")
    print("   SELECT * FROM productos LIMIT 5;")
    print("   SELECT COUNT(*) FROM ventas;")
    print("   SELECT nombre, precio FROM productos WHERE precio > 10000;")
    print("   (escribe 'salir' para volver)")
    print("="*60)
    
    while True:
        try:
            consulta = input("\nSQL> ").strip()
            
            if consulta.lower() in ['salir', 'exit', 'quit', '0']:
                print("🔙 Volviendo al menú principal...")
                break
            
            if not consulta:
                continue
            
            if not consulta.lower().startswith('select'):
                print("⚠️  Por seguridad, solo se permiten consultas SELECT")
                continue
            
            with engine.connect() as conn:
                result = conn.execute(text(consulta))
                
                # Obtener columnas
                columnas = result.keys()
                
                # Obtener datos
                datos = result.fetchall()
                
                if not datos:
                    print("📭 No se encontraron resultados")
                    continue
                
                # Mostrar resultados
                print(f"\n📊 Resultados ({len(datos)} filas):")
                print("-" * 80)
                
                # Mostrar encabezados
                for col in columnas:
                    print(f"{col:<20}", end="")
                print()
                print("-" * 80)
                
                # Mostrar datos (máximo 20 filas)
                for i, fila in enumerate(datos[:20]):
                    for valor in fila:
                        if valor is None:
                            print(f"{'NULL':<20}", end="")
                        else:
                            str_valor = str(valor)
                            if len(str_valor) > 18:
                                str_valor = str_valor[:15] + "..."
                            print(f"{str_valor:<20}", end="")
                    print()
                
                if len(datos) > 20:
                    print(f"... y {len(datos) - 20} filas más")
                
        except Exception as e:
            print(f"❌ Error en la consulta: {e}")

def consultas_predefinidas():
    """Muestra consultas SQL predefinidas útiles"""
    print("\n📈 CONSULTAS PREDEFINIDAS")
    print("="*60)
    
    consultas = {
        "1": {
            "nombre": "📊 Rango etario con más ventas",
            "sql": """
                SELECT 
                    CASE 
                        WHEN CAST(u.edad AS INTEGER) BETWEEN 18 AND 25 THEN '18-25'
                        WHEN CAST(u.edad AS INTEGER) BETWEEN 26 AND 35 THEN '26-35'
                        WHEN CAST(u.edad AS INTEGER) BETWEEN 36 AND 45 THEN '36-45'
                        WHEN CAST(u.edad AS INTEGER) BETWEEN 46 AND 55 THEN '46-55'
                        ELSE '56+'
                    END as rango_etario,
                    COUNT(v.id_venta) as total_ventas,
                    SUM(v.total_neto) as ingresos_totales,
                    AVG(v.total_neto) as promedio_venta
                FROM usuarios u
                LEFT JOIN ventas v ON u.id_usuario = v.id_usuario
                WHERE v.id_venta IS NOT NULL
                GROUP BY rango_etario
                ORDER BY total_ventas DESC;
            """
        },
        "2": {
            "nombre": "🏆 Producto más vendido (unidades)",
            "sql": """
                SELECT p.nombre as producto, p.marca,
                       SUM(v.cantidad_vendida) as unidades_vendidas,
                       COUNT(v.id_venta) as veces_vendido,
                       SUM(v.total_neto) as ingresos_totales
                FROM productos p
                JOIN ventas v ON p.id_producto = v.id_producto
                GROUP BY p.id_producto, p.nombre, p.marca
                ORDER BY unidades_vendidas DESC
                LIMIT 10;
            """
        },
        "3": {
            "nombre": "🌍 Región con mayor volumen de ventas",
            "sql": """
                SELECT d.region, 
                       COUNT(v.id_venta) as total_ventas,
                       SUM(v.total_neto) as ingresos_totales,
                       COUNT(DISTINCT v.id_usuario) as usuarios_unicos
                FROM ventas v
                JOIN tienda t ON v.id_tienda = t.id_tienda
                JOIN direccion d ON t.id_direccion = d.id_direccion
                GROUP BY d.region
                ORDER BY ingresos_totales DESC;
            """
        },
        "4": {
            "nombre": "🎯 Promoción que generó más ventas",
            "sql": """
                SELECT pr.tipo_promocion,
                       COUNT(v.id_venta) as ventas_con_promocion,
                       SUM(v.total_neto) as ingresos_totales,
                       AVG(v.total_neto) as promedio_venta,
                       COUNT(DISTINCT v.id_usuario) as usuarios_unicos
                FROM promocion pr
                JOIN ventas v ON pr.id_promocion = v.id_promocion
                GROUP BY pr.id_promocion, pr.tipo_promocion
                ORDER BY ventas_con_promocion DESC;
            """
        },
        "5": {
            "nombre": "📅 Día de la semana con más ventas",
            "sql": """
                SELECT 
                    EXTRACT(DOW FROM t.fecha) as dia_semana,
                    CASE EXTRACT(DOW FROM t.fecha)
                        WHEN 0 THEN 'Domingo'
                        WHEN 1 THEN 'Lunes'
                        WHEN 2 THEN 'Martes'
                        WHEN 3 THEN 'Miércoles'
                        WHEN 4 THEN 'Jueves'
                        WHEN 5 THEN 'Viernes'
                        WHEN 6 THEN 'Sábado'
                    END as nombre_dia,
                    COUNT(v.id_venta) as ventas,
                    SUM(v.total_neto) as ingresos_totales,
                    AVG(v.total_neto) as promedio_venta
                FROM ventas v
                JOIN tiempo t ON v.id_tiempo = t.id_tiempo
                GROUP BY dia_semana, nombre_dia
                ORDER BY ventas DESC;
            """
        },
        "6": {
            "nombre": "🛍️ Productos con promociones",
            "sql": """
                SELECT p.nombre, p.precio, p.preciofinal, pr.tipo_promocion, pr.fecha_inicio, pr.fecha_fin
                FROM productos p
                LEFT JOIN promocion pr ON p.promocion = pr.id_promocion
                WHERE p.promocion IS NOT NULL
                LIMIT 10;
            """
        },
        "7": {
            "nombre": "🏪 Ventas por tienda",
            "sql": """
                SELECT t.nombre as tienda, COUNT(v.id_venta) as total_ventas, 
                       SUM(v.total_neto) as ventas_totales
                FROM ventas v
                JOIN tienda t ON v.id_tienda = t.id_tienda
                GROUP BY t.id_tienda, t.nombre
                ORDER BY ventas_totales DESC;
            """
        },
        "8": {
            "nombre": "👥 Usuarios con más compras",
            "sql": """
                SELECT u.nombre, u.apellido, u.email, COUNT(v.id_venta) as compras,
                       SUM(v.total_neto) as total_gastado
                FROM usuarios u
                JOIN ventas v ON u.id_usuario = v.id_usuario
                GROUP BY u.id_usuario, u.nombre, u.apellido, u.email
                ORDER BY compras DESC
                LIMIT 10;
            """
        },
        "9": {
            "nombre": "🎉 Promociones activas",
            "sql": """
                SELECT tipo_promocion, fecha_inicio, fecha_fin,
                       COUNT(p.id_producto) as productos_afectados
                FROM promocion pr
                LEFT JOIN productos p ON pr.id_promocion = p.promocion
                WHERE CURRENT_DATE BETWEEN fecha_inicio AND fecha_fin
                GROUP BY pr.id_promocion, tipo_promocion, fecha_inicio, fecha_fin;
            """
        },
        "10": {
            "nombre": "📈 Ventas por mes",
            "sql": """
                SELECT t.año, t.mes, COUNT(v.id_venta) as ventas,
                       SUM(v.total_neto) as ingresos
                FROM ventas v
                JOIN tiempo t ON v.id_tiempo = t.id_tiempo
                GROUP BY t.año, t.mes
                ORDER BY t.año DESC, t.mes DESC;
            """
        }
    }
    
    while True:
        print("\n📋 CONSULTAS DISPONIBLES:")
        print("="*60)
        print("📊 ANÁLISIS DE VENTAS POR EDAD Y DEMOGRAFÍA:")
        for key in ["1", "2", "3", "4", "5"]:
            print(f"{key}. {consultas[key]['nombre']}")
        print("\n📈 CONSULTAS GENERALES:")
        for key in ["6", "7", "8", "9", "10"]:
            print(f"{key}. {consultas[key]['nombre']}")
        print("0. 🔙 Volver al menú principal")
        print("="*60)
        
        opcion = input("\nSelecciona una consulta (0-10): ").strip()
        
        if opcion == "0":
            break
        
        if opcion in consultas:
            print(f"\n🔍 Ejecutando: {consultas[opcion]['nombre']}")
            print("-" * 60)
            
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(consultas[opcion]['sql']))
                    
                    # Obtener columnas
                    columnas = result.keys()
                    
                    # Obtener datos
                    datos = result.fetchall()
                    
                    if not datos:
                        print("📭 No se encontraron resultados")
                        continue
                    
                    # Mostrar resultados
                    print(f"📊 Resultados ({len(datos)} filas):")
                    print("-" * 80)
                    
                    # Mostrar encabezados
                    for col in columnas:
                        print(f"{col:<20}", end="")
                    print()
                    print("-" * 80)
                    
                    # Mostrar datos
                    for fila in datos:
                        for valor in fila:
                            if valor is None:
                                print(f"{'NULL':<20}", end="")
                            else:
                                str_valor = str(valor)
                                if len(str_valor) > 18:
                                    str_valor = str_valor[:15] + "..."
                                print(f"{str_valor:<20}", end="")
                        print()
                    
            except Exception as e:
                print(f"❌ Error en la consulta: {e}")
        else:
            print("❌ Opción inválida. Por favor, selecciona 0-10.")

def ver_productos_con_promociones():
    """Muestra productos que tienen promociones"""
    print("\n🛍️ PRODUCTOS CON PROMOCIONES")
    print("="*60)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT p.id_producto, p.nombre, p.precio, p.preciofinal,
                       pr.tipo_promocion, pr.fecha_inicio, pr.fecha_fin,
                       t.nombre as tienda
                FROM productos p
                LEFT JOIN promocion pr ON p.promocion = pr.id_promocion
                LEFT JOIN tienda t ON p.id_tienda = t.id_tienda
                WHERE p.promocion IS NOT NULL
                ORDER BY p.id_producto
                LIMIT 20;
            """))
            
            datos = result.fetchall()
            
            if not datos:
                print("📭 No hay productos con promociones")
                return
            
            print(f"📊 Productos con promociones ({len(datos)} encontrados):")
            print("-" * 100)
            print(f"{'ID':<5} {'Producto':<30} {'Precio':<10} {'Final':<10} {'Promoción':<20} {'Tienda':<15}")
            print("-" * 100)
            
            for fila in datos:
                id_prod, nombre, precio, final, promo, inicio, fin, tienda = fila
                nombre_short = nombre[:28] + "..." if len(nombre) > 30 else nombre
                print(f"{id_prod:<5} {nombre_short:<30} {precio:<10} {final:<10} {promo:<20} {tienda:<15}")
            
    except Exception as e:
        print(f"❌ Error al consultar productos: {e}")

def ver_ventas_y_hechos():
    """Muestra información de ventas y hechos"""
    print("\n💰 VENTAS Y HECHOS")
    print("="*60)
    
    try:
        with engine.connect() as conn:
            # Estadísticas generales
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_ventas,
                    SUM(total_neto) as ingresos_totales,
                    AVG(total_neto) as promedio_venta,
                    COUNT(DISTINCT id_usuario) as usuarios_unicos,
                    COUNT(DISTINCT id_producto) as productos_vendidos
                FROM ventas;
            """))
            
            stats = result.fetchone()
            
            if stats and stats[0]:
                print("📊 ESTADÍSTICAS GENERALES:")
                print(f"   Total de ventas: {stats[0]:,}")
                print(f"   Ingresos totales: ${stats[1]:,.0f}")
                print(f"   Promedio por venta: ${stats[2]:,.0f}")
                print(f"   Usuarios únicos: {stats[3]}")
                print(f"   Productos vendidos: {stats[4]}")
            else:
                print("📭 No hay ventas registradas")
                return
            
            print("\n📈 ÚLTIMAS 10 VENTAS:")
            print("-" * 80)
            
            result = conn.execute(text("""
                SELECT v.id_venta, u.nombre, u.apellido, p.nombre as producto,
                       v.cantidad_vendida, v.total_neto, t.fecha
                FROM ventas v
                JOIN usuarios u ON v.id_usuario = u.id_usuario
                JOIN productos p ON v.id_producto = p.id_producto
                JOIN tiempo t ON v.id_tiempo = t.id_tiempo
                ORDER BY v.id_venta DESC
                LIMIT 10;
            """))
            
            datos = result.fetchall()
            
            print(f"{'ID':<5} {'Usuario':<20} {'Producto':<25} {'Cant':<5} {'Total':<10} {'Fecha':<12}")
            print("-" * 80)
            
            for fila in datos:
                id_venta, nombre, apellido, producto, cant, total, fecha = fila
                usuario = f"{nombre} {apellido}"
                producto_short = producto[:23] + "..." if len(producto) > 25 else producto
                print(f"{id_venta:<5} {usuario:<20} {producto_short:<25} {cant:<5} ${total:<9} {fecha}")
            
    except Exception as e:
        print(f"❌ Error al consultar ventas: {e}")

def ver_usuarios_y_compras():
    """Muestra usuarios y sus compras"""
    print("\n👥 USUARIOS Y SUS COMPRAS")
    print("="*60)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT u.nombre, u.apellido, u.email, u.edad, u.sexo,
                       COUNT(v.id_venta) as compras,
                       SUM(v.total_neto) as total_gastado,
                       AVG(v.total_neto) as promedio_compra
                FROM usuarios u
                LEFT JOIN ventas v ON u.id_usuario = v.id_usuario
                GROUP BY u.id_usuario, u.nombre, u.apellido, u.email, u.edad, u.sexo
                ORDER BY compras DESC, total_gastado DESC
                LIMIT 15;
            """))
            
            datos = result.fetchall()
            
            if not datos:
                print("📭 No hay usuarios registrados")
                return
            
            print(f"📊 Usuarios y sus compras ({len(datos)} usuarios):")
            print("-" * 100)
            print(f"{'Usuario':<25} {'Email':<25} {'Edad':<5} {'Compras':<8} {'Total':<12} {'Promedio':<10}")
            print("-" * 100)
            
            for fila in datos:
                nombre, apellido, email, edad, sexo, compras, total, promedio = fila
                usuario = f"{nombre} {apellido}"
                email_short = email[:23] + "..." if len(email) > 25 else email
                total_str = f"${total:,.0f}" if total else "$0"
                promedio_str = f"${promedio:,.0f}" if promedio else "$0"
                
                print(f"{usuario:<25} {email_short:<25} {edad:<5} {compras:<8} {total_str:<12} {promedio_str:<10}")
            
    except Exception as e:
        print(f"❌ Error al consultar usuarios: {e}")

def main():
    """Función principal del consultor SQL"""
    while True:
        mostrar_menu_principal()
        
        try:
            opcion = input("\nSelecciona una opción (0-6): ").strip()
            
            if opcion == "1":
                ver_todas_las_tablas()
                input("\nPresiona Enter para continuar...")
                
            elif opcion == "2":
                consulta_sql_personalizada()
                
            elif opcion == "3":
                consultas_predefinidas()
                
            elif opcion == "4":
                ver_productos_con_promociones()
                input("\nPresiona Enter para continuar...")
                
            elif opcion == "5":
                ver_ventas_y_hechos()
                input("\nPresiona Enter para continuar...")
                
            elif opcion == "6":
                ver_usuarios_y_compras()
                input("\nPresiona Enter para continuar...")
                
            elif opcion == "0":
                print("\n👋 ¡Volviendo al menú principal!")
                break
                
            else:
                print("❌ Opción inválida. Por favor, selecciona 0-6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Volviendo al menú principal!")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main() 