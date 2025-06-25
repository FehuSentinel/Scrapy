import os
from sqlalchemy import create_engine, text
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

def verificar_estructura_tabla():
    """Verifica la estructura real de la tabla usuarios"""
    print("🔍 VERIFICANDO ESTRUCTURA DE LA TABLA 'usuarios'")
    print("=" * 60)
    
    try:
        with engine.connect() as conn:
            # Verificar si la tabla existe
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'usuarios'
                );
            """))
            tabla_existe = result.scalar()
            
            if not tabla_existe:
                print("❌ La tabla 'usuarios' NO existe en la base de datos")
                return
            
            print("✅ La tabla 'usuarios' existe")
            
            # Obtener estructura de la tabla
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'usuarios'
                ORDER BY ordinal_position;
            """))
            
            columnas = result.fetchall()
            
            print(f"\n📋 Estructura actual de la tabla 'usuarios':")
            print("-" * 60)
            print(f"{'Columna':<15} {'Tipo':<15} {'Nullable':<10} {'Default'}")
            print("-" * 60)
            
            for columna in columnas:
                nombre = columna[0]
                tipo = columna[1]
                nullable = columna[2]
                default = columna[3] or 'NULL'
                print(f"{nombre:<15} {tipo:<15} {nullable:<10} {default}")
            
            # Verificar si falta la columna direccion
            columnas_nombres = [col[0] for col in columnas]
            if 'direccion' not in columnas_nombres:
                print(f"\n⚠️  PROBLEMA DETECTADO:")
                print(f"   La columna 'direccion' NO existe en la tabla")
                print(f"   Columnas encontradas: {', '.join(columnas_nombres)}")
                
                # Preguntar si agregar la columna
                respuesta = input(f"\n¿Deseas agregar la columna 'direccion'? (s/n): ").lower()
                if respuesta == 's':
                    try:
                        conn.execute(text("""
                            ALTER TABLE usuarios 
                            ADD COLUMN direccion VARCHAR(255);
                        """))
                        conn.commit()
                        print("✅ Columna 'direccion' agregada exitosamente")
                    except Exception as e:
                        print(f"❌ Error al agregar la columna: {e}")
                        conn.rollback()
            else:
                print(f"\n✅ La columna 'direccion' existe correctamente")
                
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")

if __name__ == "__main__":
    verificar_estructura_tabla() 