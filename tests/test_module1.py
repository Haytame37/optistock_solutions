from core.logistique import haversine, calculer_score_mixte

# --- ÉTAPE 1 : IMPORTATION DES DONNÉES (Catalogue fictif) ---
entrepots_catalogue = [
    {"id": 1, "nom": "Hub Casablanca", "lat": 33.57, "lon": -7.58, "type": "Froid", "t_ok": 98, "h_ok": 95},
    {"id": 2, "nom": "Entrepôt Béni Mellal", "lat": 32.33, "lon": -6.35, "type": "Sec", "t_ok": 90, "h_ok": 85},
    {"id": 3, "nom": "Zone Tanger Med", "lat": 35.87, "lon": -5.51, "type": "Froid", "t_ok": 75, "h_ok": 70},
    {"id": 4, "nom": "Plateforme Marrakech", "lat": 31.63, "lon": -7.98, "type": "Froid", "t_ok": 92, "h_ok": 88},
]

# --- ÉTAPE 2 : SAISIE DES BESOINS CLIENT (Entrées du système) ---
client_gps = (33.58, -7.60) # Coordonnées du point de livraison (ex: Casablanca Centre)
type_requis = "Froid"       # Contrainte spécifique

# Le client choisit ses priorités (doit totaliser 1.0)
poids_client = {
    'dist': 0.5,  # 50% d'importance pour la proximité
    'temp': 0.3,  # 30% pour la stabilité thermique
    'hum': 0.2    # 20% pour l'humidité
}

print(f"--- ANALYSE POUR : Type {type_requis} | Point de livraison {client_gps} ---")

# --- ÉTAPE 3 : CALCULS ET FILTRAGE ---
resultats_finaux = []

for e in entrepots_catalogue:
    # Filtre sur le type de stockage (Besoin spécifique)
    if e['type'] == type_requis:
        # Calcul Haversine
        distance_km = haversine(client_gps[0], client_gps[1], e['lat'], e['lon'])
        
        # Calcul du Score Mixte
        score = calculer_score_mixte(distance_km, e['t_ok'], e['h_ok'], poids_client)
        
        resultats_finaux.append({
            "nom": e['nom'],
            "distance": round(distance_km, 2),
            "score": score,
            "iot_status": f"T:{e['t_ok']}% | H:{e['h_ok']}%"
        })

# --- ÉTAPE 4 : CLASSEMENT ET SORTIE ---
classement = sorted(resultats_finaux, key=lambda x: x['score'], reverse=True)

print(f"{'Rang':<5} | {'Nom':<20} | {'Distance':<10} | {'Score/100':<10} | {'Détails IoT'}")
print("-" * 70)
for i, res in enumerate(classement, 1):
    print(f"{i:<5} | {res['nom']:<20} | {res['distance']:<7} km | {res['score']:<10} | {res['iot_status']}")