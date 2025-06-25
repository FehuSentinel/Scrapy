import requests
import pandas as pd
import os

# Solicitar cantidad de usuarios
users = input("Ingrese cantidad de usuarios a generar: ")

# Validar si la entrada es un número
if not users.isdigit() or int(users) <= 0:
    print("Por favor, ingrese un número válido mayor que 0.")
    exit()

# Construir la URL de la API
url = f"https://randomuser.me/api/?results={users}"
response = requests.get(url)

# Validar respuesta de la API
if response.status_code != 200:
    print("Error al conectar con RandomUser API:", response.status_code)
    exit()

# Procesar los datos
data = response.json()["results"]

usuarios = []
for user in data:
    usuarios.append({
        "nombre": user["name"]["first"],
        "apellido": user["name"]["last"],
        "email": user["email"],
        "direccion": user["location"]["city"],
    })

# Crear DataFrame
df = pd.DataFrame(usuarios)

# Crear carpeta 'archivos' si no existe
carpeta_archivos = 'archivos'
if not os.path.exists(carpeta_archivos):
    os.makedirs(carpeta_archivos)
    print(f"✅ Carpeta '{carpeta_archivos}' creada exitosamente.")

# Solicitar nombre del archivo
nombre_archivo = input("Ingrese el nombre del archivo (sin extensión): ")

# Guardar CSV en la carpeta archivos
csv_filename = os.path.join(carpeta_archivos, f"{nombre_archivo}.csv")
df.to_csv(csv_filename, index=False, encoding="utf-8-sig")

# Guardar Excel en la carpeta archivos
excel_filename = os.path.join(carpeta_archivos, f"{nombre_archivo}.xlsx")
df.to_excel(excel_filename, index=False)

print(f"✅ Archivos guardados en la carpeta '{carpeta_archivos}':")
print(f"   - {csv_filename}")
print(f"   - {excel_filename}")
