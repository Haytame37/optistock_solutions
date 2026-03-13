import pandas as pd

def traiter_recommandation_csv(path_entrepots, path_iot, path_trajets, poids_client):
    # 1. Importation des données
    df_entrepots = pd.read_csv(path_entrepots)
    df_iot = pd.read_csv(path_iot)
    df_trajets = pd.read_csv(path_trajets)
    
    # 2. Prétraitement IoT : Calcul de la conformité moyenne par entrepôt
    # (Exemple: % de relevés où temp < 5°C pour le froid)
    stats_iot = df_iot.groupby('nom_entrepot').agg({
        'temperature': lambda x: (x < 8).mean() * 100, # % de conformité froid
        'humidite': 'mean'
    }).reset_index()
    
    # 3. Logique de recommandation pour chaque trajet client
    recommandations = []
    
    for _, trajet in df_trajets.iterrows():
        # Filtrer le catalogue selon le besoin spécifique (Froid/Sec)
        disponibles = df_entrepots[df_entrepots['type_stockage'] == trajet['type_requis']]
        
        # Calculer les scores pour cet entrepôt
        scores_trajet = []
        for _, ent in disponibles.iterrows():
            # Distance Haversine
            d = haversine(trajet['lat'], trajet['lon'], ent['lat'], ent['lon'])
            
            # Récupérer les stats IoT correspondantes
            iot = stats_iot[stats_iot['nom_entrepot'] == ent['nom']].iloc[0]
            
            # Calcul du score final S = Σ(Ci * Wi)
            s = calculer_score_mixte(d, iot['temperature'], iot['humidite'], poids_client)
            
            scores_trajet.append({
                'client': trajet['client_id'],
                'entrepot': ent['nom'],
                'distance': round(d, 2),
                'score': s
            })
        
        # Garder le meilleur entrepôt pour ce client
        meilleur = max(scores_trajet, key=lambda x: x['score'])
        recommandations.append(meilleur)
        
    return pd.DataFrame(recommandations)

def calculer_centre_gravite(points_livraison):
    """
    Calcule le point optimal (Lat, Lon) pour une nouvelle implantation.
    points_livraison: Liste de dictionnaires [{'lat': float, 'lon': float, 'volume': float}]
    """
    total_volume = sum(p['volume'] for p in points_livraison)
    
    if total_volume == 0:
        return None, None

    # Formule : Σ (Coordonnée * Volume) / Σ Volume
    lat_optimal = sum(p['lat'] * p['volume'] for p in points_livraison) / total_volume
    lon_optimal = sum(p['lon'] * p['volume'] for p in points_livraison) / total_volume
    
    return round(lat_optimal, 4), round(lon_optimal, 4)