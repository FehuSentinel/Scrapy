import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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
Session = sessionmaker(bind=engine)
session = Session()

def ver_usuarios():
    """Muestra los usuarios en la base de datos con paginación"""
    print("👥 USUARIOS EN LA BASE DE DATOS")
    print("=" * 60)
    
    usuarios = session.query(models.Usuario).all()
    
    if not usuarios:
        print("📭 No hay usuarios en la base de datos")
        return
    
    print(f"📊 Total de usuarios: {len(usuarios)}")
    
    # Configuración de paginación
    elementos_por_pagina = 10
    pagina_actual = 0
    total_paginas = (len(usuarios) + elementos_por_pagina - 1) // elementos_por_pagina
    
    while True:
        # Calcular índices de inicio y fin
        inicio = pagina_actual * elementos_por_pagina
        fin = min(inicio + elementos_por_pagina, len(usuarios))
        
        print(f"\n📋 Página {pagina_actual + 1} de {total_paginas}")
        print("-" * 60)
        
        # Mostrar usuarios de la página actual
        for i in range(inicio, fin):
            usuario = usuarios[i]
            print(f"{i+1:3d}. {usuario.Nombre} {usuario.apellido}")
            print(f"     Email: {usuario.email}")
            print(f"     Dirección: {usuario.direccion}")
            print(f"     ID: {usuario.id_usuario}")
            print()
        
        # Mostrar opciones de navegación
        print("=" * 60)
        if total_paginas > 1:
            if pagina_actual > 0:
                print("1. ⬅️  Página anterior")
            if pagina_actual < total_paginas - 1:
                print("2. ➡️  Página siguiente")
            print("3. 🏠 Volver al menú de tablas")
            
            while True:
                opcion = input("\nSelecciona una opción: ").strip()
                
                if opcion == "1" and pagina_actual > 0:
                    pagina_actual -= 1
                    break
                elif opcion == "2" and pagina_actual < total_paginas - 1:
                    pagina_actual += 1
                    break
                elif opcion == "3":
                    return
                else:
                    print("❌ Opción inválida. Intenta de nuevo.")
        else:
            input("\nPresiona Enter para volver al menú de tablas...")
            return

def ver_tiendas():
    """Muestra las tiendas en la base de datos con paginación"""
    print("🏪 TIENDAS EN LA BASE DE DATOS")
    print("=" * 50)
    
    tiendas = session.query(models.Tienda).all()
    
    if not tiendas:
        print("📭 No hay tiendas en la base de datos")
        return
    
    print(f"📊 Total de tiendas: {len(tiendas)}")
    
    # Configuración de paginación
    elementos_por_pagina = 10
    pagina_actual = 0
    total_paginas = (len(tiendas) + elementos_por_pagina - 1) // elementos_por_pagina
    
    while True:
        # Calcular índices de inicio y fin
        inicio = pagina_actual * elementos_por_pagina
        fin = min(inicio + elementos_por_pagina, len(tiendas))
        
        print(f"\n📋 Página {pagina_actual + 1} de {total_paginas}")
        print("-" * 50)
        
        # Mostrar tiendas de la página actual
        for i in range(inicio, fin):
            tienda = tiendas[i]
            print(f"   ID: {tienda.id_tienda} | Nombre: {tienda.nombre}")
            if tienda.direccion:
                print(f"        Dirección: {tienda.direccion}")
            if tienda.url:
                print(f"        URL: {tienda.url}")
            print()
        
        # Mostrar opciones de navegación
        print("=" * 50)
        if total_paginas > 1:
            if pagina_actual > 0:
                print("1. ⬅️  Página anterior")
            if pagina_actual < total_paginas - 1:
                print("2. ➡️  Página siguiente")
            print("3. 🏠 Volver al menú de tablas")
            
            while True:
                opcion = input("\nSelecciona una opción: ").strip()
                
                if opcion == "1" and pagina_actual > 0:
                    pagina_actual -= 1
                    break
                elif opcion == "2" and pagina_actual < total_paginas - 1:
                    pagina_actual += 1
                    break
                elif opcion == "3":
                    return
                else:
                    print("❌ Opción inválida. Intenta de nuevo.")
        else:
            input("\nPresiona Enter para volver al menú de tablas...")
            return

def ver_productos():
    """Muestra los productos en la base de datos con paginación"""
    print("🛍️ PRODUCTOS EN LA BASE DE DATOS")
    print("=" * 60)
    
    productos = session.query(models.Producto).all()
    
    if not productos:
        print("📭 No hay productos en la base de datos")
        return
    
    print(f"📊 Total de productos: {len(productos)}")
    
    # Configuración de paginación
    elementos_por_pagina = 10
    pagina_actual = 0
    total_paginas = (len(productos) + elementos_por_pagina - 1) // elementos_por_pagina
    
    while True:
        # Calcular índices de inicio y fin
        inicio = pagina_actual * elementos_por_pagina
        fin = min(inicio + elementos_por_pagina, len(productos))
        
        print(f"\n📋 Página {pagina_actual + 1} de {total_paginas}")
        print("-" * 60)
        
        # Mostrar productos de la página actual
        for i in range(inicio, fin):
            producto = productos[i]
            print(f"{i+1:3d}. {producto.nombre[:50]}...")
            print(f"     Tienda: {producto.tienda}")
            print(f"     Marca: {producto.marca or 'N/A'}")
            print(f"     Precio: {producto.precio or 'N/A'}")
            print(f"     ID: {producto.id_producto}")
            print()
        
        # Mostrar opciones de navegación
        print("=" * 60)
        if total_paginas > 1:
            if pagina_actual > 0:
                print("1. ⬅️  Página anterior")
            if pagina_actual < total_paginas - 1:
                print("2. ➡️  Página siguiente")
            print("3. 🏠 Volver al menú de tablas")
            
            while True:
                opcion = input("\nSelecciona una opción: ").strip()
                
                if opcion == "1" and pagina_actual > 0:
                    pagina_actual -= 1
                    break
                elif opcion == "2" and pagina_actual < total_paginas - 1:
                    pagina_actual += 1
                    break
                elif opcion == "3":
                    # Mostrar estadísticas antes de salir
                    mostrar_estadisticas_productos()
                    return
                else:
                    print("❌ Opción inválida. Intenta de nuevo.")
        else:
            # Mostrar estadísticas si solo hay una página
            mostrar_estadisticas_productos()
            input("\nPresiona Enter para volver al menú de tablas...")
            return

def mostrar_estadisticas_productos():
    """Muestra estadísticas de productos por tienda"""
    print("\n📈 ESTADÍSTICAS POR TIENDA:")
    print("-" * 30)
    
    from sqlalchemy import func
    stats = session.query(
        models.Producto.tienda,
        func.count(models.Producto.id_producto).label('cantidad')
    ).group_by(models.Producto.tienda).all()
    
    for tienda, cantidad in stats:
        print(f"   {tienda}: {cantidad} productos")

def mostrar_menu():
    """Muestra el menú de opciones"""
    print("\n" + "="*50)
    print("    🗄️  VISOR DE TABLAS DE LA BASE DE DATOS")
    print("="*50)
    print("1. 👥 Ver usuarios")
    print("2. 🏪 Ver tiendas")
    print("3. 🛍️ Ver productos")
    print("0. 🚪 Volver al menú principal")
    print("="*50)

def main():
    """Función principal"""
    while True:
        mostrar_menu()
        
        try:
            opcion = input("\nSelecciona una opción (0-3): ").strip()
            
            if opcion == "1":
                ver_usuarios()
                input("\nPresiona Enter para continuar...")
                
            elif opcion == "2":
                ver_tiendas()
                input("\nPresiona Enter para continuar...")
                
            elif opcion == "3":
                ver_productos()
                input("\nPresiona Enter para continuar...")
                
            elif opcion == "0":
                print("\n👋 ¡Volviendo al menú principal!")
                break
                
            else:
                print("❌ Opción inválida. Por favor, selecciona 0, 1, 2 o 3.")
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Volviendo al menú principal!")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main() 