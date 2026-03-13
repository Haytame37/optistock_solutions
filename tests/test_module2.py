import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.logistique import calculer_centre_gravite

# Données fictives (3 clients au Maroc)
clients = [
    {"nom": "Client Casa", "lat": 33.57, "lon": -7.58, "volume": 1000},
    {"nom": "Client Fès", "lat": 34.03, "lon": -5.00, "volume": 200},
    {"nom": "Client Marrakech", "lat": 31.63, "lon": -7.98, "volume": 150}
]

lat_opt, lon_opt = calculer_centre_gravite(clients)

print(f"--- TEST MODULE 2 ---")
print(f"Point optimal calculé : Lat {lat_opt}, Lon {lon_opt}")
# Le point devrait être proche de Casablanca car c'est le plus gros volume.