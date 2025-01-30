import csv
import time
import requests
import mysql.connector
from datetime import datetime
import schedule

# Configuración
API_KEY = "AIzaSyDIzpr-nfRkt--htgdQNnOwvXM4o2rkksk"  # Reemplázalo con una API Key segura
LIMIT = 100  # Cantidad de localidades por ejecución
BUSQUEDA = "repuestos de motos"  # Cambia esto cuando termines con una categoría

# Conexión a MySQL
def conectar_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="scraping"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error de conexión: {err}")
        return None

def obtener_localidades(conn):
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id, provincia, localidad FROM localidades WHERE procesado = 0 LIMIT %s"
    cursor.execute(query, (LIMIT,))
    localidades = cursor.fetchall()
    cursor.close()
    return localidades

def buscar_repuestos(localidad, provincia, api_key, busqueda):
    query = f"{busqueda} {localidad} {provincia}"
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={api_key}&language=es&region=AR"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Error en la solicitud: {response.status_code}")
        return []
    return response.json().get("results", [])

def obtener_detalles(place_id, api_key):
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_phone_number,formatted_address,website,email,opening_hours,rating&key={api_key}&language=es"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Error en la solicitud: {response.status_code}")
        return {}
    return response.json().get("result", {})

def procesar_localidades():
    conn = conectar_db()
    if not conn:
        return
    
    localidades = obtener_localidades(conn)
    if not localidades:
        print("❌ No hay más localidades pendientes.")
        conn.close()
        return
    
    output_csv = "repuestos_motos_corregido.csv"
    with open(output_csv, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Provincia", "Localidad", "Nombre", "Dirección", "Teléfono", "Correo", "Sitio Web", "Rating"])

        for localidad in localidades:
            resultados = buscar_repuestos(localidad["localidad"], localidad["provincia"], API_KEY, BUSQUEDA)
            cursor = conn.cursor()

            if not resultados:
                cursor.execute("UPDATE localidades SET procesado = 1 WHERE id = %s", (localidad["id"],))
                conn.commit()
                cursor.close()
                continue

            for res in resultados:
                detalles = obtener_detalles(res["place_id"], API_KEY)
                writer.writerow([
                    localidad["provincia"],
                    localidad["localidad"],
                    detalles.get("name", res.get("name", "")),
                    detalles.get("formatted_address", res.get("formatted_address", "")),
                    detalles.get("formatted_phone_number", ""),
                    detalles.get("email", ""),
                    detalles.get("website", ""),
                    detalles.get("rating", res.get("rating", ""))
                ])
            
            cursor.execute("UPDATE localidades SET procesado = 1 WHERE id = %s", (localidad["id"],))
            conn.commit()
            cursor.close()
            print(f"✅ Localidad procesada: {localidad['localidad']}")
            time.sleep(2)
    
    conn.close()
    print(f"✅ Extracción completada. Datos guardados en {output_csv}.")

# Programar ejecución diaria a las 11:37 PM
schedule.every().day.at("11:37").do(procesar_localidades)

print("⏳ Job iniciado. Ejecutando diariamente a las 11:37 PM...")
while True:
    schedule.run_pending()
    time.sleep(60)
