import requests
import csv
import time

# Tu clave de API de Google Maps
API_KEY = "AIzaSyDIzpr-nfRkt--htgdQNnOwvXM4o2rkksk"

# Diccionario de provincias argentinas y sus principales ciudades
provincias_ciudades = {
    "Buenos Aires": ["La Plata", "Mar del Plata", "Bahía Blanca", "Tandil", "Luján"],
    "Catamarca": ["San Fernando del Valle de Catamarca", "Belén", "Tinogasta", "Santa María"],
    "Chaco": ["Resistencia", "Presidencia Roque Sáenz Peña", "Villa Ángela", "Charata"],
    "Chubut": ["Rawson", "Trelew", "Puerto Madryn", "Esquel", "Comodoro Rivadavia"],
    "Córdoba": ["Córdoba", "Villa Carlos Paz", "Río Cuarto", "Villa María", "San Francisco"],
    "Corrientes": ["Corrientes", "Goya", "Mercedes", "Paso de los Libres", "Curuzú Cuatiá"],
    "Entre Ríos": ["Paraná", "Concordia", "Gualeguaychú", "Gualeguay", "Colón"],
    "Formosa": ["Formosa", "Clorinda", "Pirané", "El Colorado", "Laguna Blanca"],
    "Jujuy": ["San Salvador de Jujuy", "Palpalá", "Perico", "Libertador General San Martín", "Tilcara"],
    "La Pampa": ["Santa Rosa", "General Pico", "Toay", "Victorica", "Macachín"],
    "La Rioja": ["La Rioja", "Chilecito", "Chamical", "Aimogasta", "Villa Unión"],
    "Mendoza": ["Mendoza", "San Rafael", "Godoy Cruz", "Luján de Cuyo", "Maipú"],
    "Misiones": ["Posadas", "Oberá", "Eldorado", "Puerto Iguazú", "Leandro N. Alem"],
    "Neuquén": ["Neuquén", "San Martín de los Andes", "Zapala", "Plottier", "Centenario"],
    "Río Negro": ["Viedma", "San Carlos de Bariloche", "General Roca", "Cipolletti", "Villa Regina"],
    "Salta": ["Salta", "Tartagal", "Orán", "Rosario de la Frontera", "Cafayate"],
    "San Juan": ["San Juan", "Rawson", "Chimbas", "Rivadavia", "Pocito"],
    "San Luis": ["San Luis", "Villa Mercedes", "Merlo", "La Punta", "Juana Koslay"],
    "Santa Cruz": ["Río Gallegos", "Caleta Olivia", "El Calafate", "Pico Truncado", "Puerto Deseado"],
    "Santa Fe": ["Santa Fe", "Rosario", "Rafaela", "Venado Tuerto", "Reconquista"],
    "Santiago del Estero": ["Santiago del Estero", "La Banda", "Termas de Río Hondo", "Frías", "Añatuya"],
    "Tierra del Fuego": ["Ushuaia", "Río Grande", "Tolhuin"],
    "Tucumán": ["San Miguel de Tucumán", "Tafí Viejo", "Concepción", "Yerba Buena", "Banda del Río Salí"]
}

# Parámetros de búsqueda
# query = "repuestos gomerias"
query = "gomerias"
url_textsearch = "https://maps.googleapis.com/maps/api/place/textsearch/json"
url_details = "https://maps.googleapis.com/maps/api/place/details/json"

# Archivo de salida
# output_file = "repuestos_motos_argentina.csv"
output_file = "gomerias_argentina.csv"

# Lista para evitar duplicados
processed_place_ids = set()

# Crear o limpiar el archivo CSV
with open(output_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Provincia", "Ciudad", "Nombre del Lugar", "Ubicación", "Teléfono"])

def fetch_places(query, city, page_token=None):
    """Obtiene lugares para una ciudad específica."""
    params = {
        "query": f"{query} en {city}",
        "key": API_KEY
    }
    if page_token:
        params["pagetoken"] = page_token

    response = requests.get(url_textsearch, params=params)
    response_data = response.json()
    return response_data

def fetch_place_details(place_id):
    """Obtiene detalles de un lugar usando su place_id."""
    params = {
        "place_id": place_id,
        "fields": "name,formatted_phone_number,formatted_address",
        "key": API_KEY
    }

    response = requests.get(url_details, params=params)
    response_data = response.json()
    return response_data

def save_to_csv(provincia, city, name, address, phone):
    """Guarda los datos en un archivo CSV."""
    with open(output_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([provincia, city, name, address, phone])

def process_city(provincia, city):
    """Procesa una ciudad completa, incluyendo paginación y detalles."""
    print(f"  Procesando ciudad: {city} en {provincia}")
    page_token = None
    total_results = 0

    while total_results < 800:
        # Buscar lugares
        response_data = fetch_places(query, city, page_token)

        if "results" not in response_data:
            print(f"    No se encontraron resultados para {city}.")
            break

        for place in response_data["results"]:
            place_id = place["place_id"]

            if place_id in processed_place_ids:
                continue

            # Marcar el lugar como procesado
            processed_place_ids.add(place_id)

            # Obtener detalles del lugar
            details_response = fetch_place_details(place_id)
            result = details_response.get("result", {})

            # Extraer información
            name = result.get("name")
            address = result.get("formatted_address")
            phone = result.get("formatted_phone_number")

            # Solo guardar si hay teléfono
            if phone:
                save_to_csv(provincia, city, name, address, phone)
                total_results += 1

            if total_results >= 800:
                break

        # Manejar la paginación
        page_token = response_data.get("next_page_token")
        if not page_token:
            break

        # Esperar para cumplir con las políticas de Google
        time.sleep(2)

def process_province(provincia, cities):
    """Procesa una provincia completa iterando por sus ciudades."""
    print(f"Procesando provincia: {provincia}")
    for city in cities:
        process_city(provincia, city)

# Procesar cada provincia
for provincia, cities in provincias_ciudades.items():
    process_province(provincia, cities)

print("Proceso completado. Los resultados se guardaron en el archivo CSV.")
