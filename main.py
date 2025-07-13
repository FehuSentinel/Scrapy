import os
import sys
import subprocess
import time

def mostrar_menu():
    """Muestra el menú principal"""
    print("\n" + "="*50)
    print("    🗄️  GESTOR DE DATOS POSTGRESQL")
    print("="*50)
    print("1. 🚀 Scraper Integrado (Datos Completos)")
    print("2. 📁 Cargar archivo CSV a la base de datos")
    print("3. 📂 Ver archivos disponibles")
    print("4. 🔍 Consultar DB conectada")
    print("0. 🚪 Salir")
    print("="*50)

def ejecutar_scrapyuser():
    """Ejecuta el script de generación de datos"""
    print("\n🔄 Iniciando generación de datos...")
    try:
        subprocess.run([sys.executable, "scrapyuser.py"], check=True)
        print("✅ Generación completada exitosamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar scrapyuser.py: {e}")
    except FileNotFoundError:
        print("❌ No se encontró el archivo scrapyuser.py")

def ejecutar_scrapy_productos():
    """Ejecuta el script de scraping de productos"""
    print("\n🔄 Iniciando scraping de productos...")
    try:
        subprocess.run([sys.executable, "scrapyProductos.py"], check=True)
        print("✅ Scraping completado exitosamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar scrapyProductos.py: {e}")
    except FileNotFoundError:
        print("❌ No se encontró el archivo scrapyProductos.py")

def ejecutar_scrapy_integrado():
    """Ejecuta el script de scraper integrado para datos completos"""
    print("\n🔄 Iniciando scraper integrado...")
    print("📋 Este scraper generará AUTOMÁTICAMENTE:")
    print("   👥 Usuarios aleatorios con edad y sexo")
    print("   🛍️ Productos reales con promociones extraídas")
    print("   🏪 Direcciones reales de tiendas")
    print("   ⏰ Fechas aleatorias pero realistas")
    print("   💰 Ventas simuladas basadas en rangos etarios")
    print("   📊 Un solo archivo con toda la información")
    print("   🎯 Promociones reales extraídas de los productos")
    print("   🗓️ Tabla tiempo con fechas de promociones")
    print()
    try:
        subprocess.run([sys.executable, "scrapy_integrado.py"], check=True)
        print("✅ Scraper integrado completado exitosamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar scrapy_integrado.py: {e}")
    except FileNotFoundError:
        print("❌ No se encontró el archivo scrapy_integrado.py")

def ejecutar_cargar_csv():
    """Ejecuta el script de carga de CSV"""
    print("\n🔄 Iniciando carga de archivo CSV...")
    try:
        # Ejecutar de manera interactiva para permitir input del usuario
        subprocess.run([sys.executable, "cargar_csv.py"], check=True)
        print("✅ Carga completada exitosamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar cargar_csv.py: {e}")
    except FileNotFoundError:
        print("❌ No se encontró el archivo cargar_csv.py")

def ver_archivos_disponibles():
    """Muestra los archivos CSV disponibles en la carpeta archivos"""
    carpeta_archivos = 'archivos'
    
    if not os.path.exists(carpeta_archivos):
        print(f"\n📂 La carpeta '{carpeta_archivos}' no existe.")
        print("💡 Ejecuta la opción 1 (Scraper Integrado) para generar datos y crear la carpeta.")
        time.sleep(3)
        return
    
    archivos_csv = [f for f in os.listdir(carpeta_archivos) if f.endswith('.csv')]
    
    if not archivos_csv:
        print(f"\n📂 No hay archivos CSV en la carpeta '{carpeta_archivos}'.")
        print("💡 Ejecuta la opción 1 (Scraper Integrado) para generar algunos datos.")
        time.sleep(3)
        return
    
    print(f"\n📂 Archivos CSV disponibles en '{carpeta_archivos}/':")
    for i, archivo in enumerate(archivos_csv, 1):
        ruta_completa = os.path.join(carpeta_archivos, archivo)
        tamaño = os.path.getsize(ruta_completa)
        print(f"   {i}. {archivo} ({tamaño:,} bytes)")
    time.sleep(3)

def ejecutar_ver_tablas():
    """Ejecuta el consultor SQL de la base de datos"""
    print("\n🔄 Abriendo consultor SQL...")
    try:
        # Ejecutar de manera interactiva para permitir navegación
        subprocess.run([sys.executable, "ver_tablas_db.py"], check=True)
        print("✅ Consultor SQL cerrado")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar ver_tablas_db.py: {e}")
    except FileNotFoundError:
        print("❌ No se encontró el archivo ver_tablas_db.py")

def main():
    """Función principal del programa"""
    while True:
        mostrar_menu()
        
        try:
            opcion = input("\nSelecciona una opción (0-4): ").strip()
            
            if opcion == "1":
                ejecutar_scrapy_integrado()
                
            elif opcion == "2":
                ejecutar_cargar_csv()
                
            elif opcion == "3":
                ver_archivos_disponibles()
                
            elif opcion == "4":
                ejecutar_ver_tablas()
                
            elif opcion == "0":
                print("\n👋 ¡Hasta luego!")
                break
                
            else:
                print("❌ Opción inválida. Por favor, selecciona 0, 1, 2, 3 o 4.")
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main() 