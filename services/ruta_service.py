import requests
import json
from flask import current_app

class RutaService:
    
    @staticmethod
    def obtener_coordenadas(direccion):
        """Geocodificar dirección a coordenadas usando Nominatim"""
        try:
            url = f"https://nominatim.openstreetmap.org/search"
            params = {
                'q': direccion,
                'format': 'json',
                'limit': 1
            }
            response = requests.get(url, params=params, headers={'User-Agent': 'TransportApp/1.0'})
            data = response.json()
            if data:
                return [float(data[0]['lat']), float(data[0]['lon'])]
            return None
        except Exception as e:
            current_app.logger.error(f"Error geocodificando {direccion}: {e}")
            return None
    
    @staticmethod
    def calcular_ruta(origen_coords, destino_coords):
        """
        Calcular ruta usando OSRM respetando el sentido de las calles
        OSRM ya considera las calles de sentido único por defecto
        """
        try:
            # OSRM espera formato lon,lat
            start = f"{origen_coords[1]},{origen_coords[0]}"
            end = f"{destino_coords[1]},{destino_coords[0]}"
            
            url = f"http://router.project-osrm.org/route/v1/driving/{start};{end}"
            params = {
                'overview': 'full',
                'geometries': 'geojson',
                'steps': 'true'  # Para obtener instrucciones detalladas
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['code'] == 'Ok' and data['routes']:
                route = data['routes'][0]
                
                # Convertir coordenadas de [lon, lat] a [lat, lon]
                coords = [[c[1], c[0]] for c in route['geometry']['coordinates']]
                
                return {
                    'coordenadas': coords,
                    'duracion': round(route['duration'] / 60),  # minutos
                    'distancia': round(route['distance'] / 1000, 1),  # km
                    'instrucciones': route['legs'][0]['steps'] if 'steps' in route else []
                }
            return None
            
        except Exception as e:
            current_app.logger.error(f"Error calculando ruta: {e}")
            return None
    
    @staticmethod
    def crear_ruta_completa(nombre, origen, destino):
        """
        Crear una ruta con sentido de ida y vuelta
        La vuelta es la ruta inversa pero respetando el sentido de las calles
        """
        # Obtener coordenadas de origen y destino
        origen_coords = RutaService.obtener_coordenadas(origen)
        destino_coords = RutaService.obtener_coordenadas(destino)
        
        if not origen_coords or not destino_coords:
            return None
        
        # Ruta de ida: origen -> destino
        ruta_ida = RutaService.calcular_ruta(origen_coords, destino_coords)
        
        # Ruta de vuelta: destino -> origen (OSRM calcula respetando sentidos)
        ruta_vuelta = RutaService.calcular_ruta(destino_coords, origen_coords)
        
        if not ruta_ida or not ruta_vuelta:
            return None
        
        return {
            'nombre': nombre,
            'origen': origen,
            'destino': destino,
            'ida': {
                'coordenadas': ruta_ida['coordenadas'],
                'duracion': ruta_ida['duracion'],
                'distancia': ruta_ida['distancia']
            },
            'vuelta': {
                'coordenadas': ruta_vuelta['coordenadas'],
                'duracion': ruta_vuelta['duracion'],
                'distancia': ruta_vuelta['distancia']
            }
        }