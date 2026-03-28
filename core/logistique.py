import pandas as pd
import numpy as np
def calculer_distances_haversine_vectorise(lat1, lon1, lat2, lon2):
    """
    Calcule la distance Haversine de manière vectorisée avec NumPy.
    Idéal pour traiter des DataFrames complets sans utiliser de boucles.
    
    Arguments:
    lat1, lon1 : Séries Pandas ou tableaux NumPy (ex: Coordonnées des livraisons)
    lat2, lon2 : Séries Pandas ou tableaux NumPy (ex: Coordonnées de l'entrepôt)

    Retourne:
    la distance entre les deux points
    """
    # Rayon moyen de la Terre en kilomètres
    R = 6371.0

    # Conversion de toutes les coordonnées de degrés en radians en une seule passe
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    # Calcul des différences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Application de la formule vectorisée
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    # Retourne les distances
    return R * c


def analyser_demandes_et_localiser(df_demandes):
    """
    Calcule le centre de stockage optimal en minimisant le coût total de transport
    via le modèle de gravité itératif (Network Optimization Model).
    Attends un DataFrame avec les colonnes: ['ville', 'lat', 'lon', 'demande', 'tarif_transport']
    """
    if 'tarif_transport' not in df_demandes.columns:
        raise ValueError("La colonne 'tarif_transport' est requise pour le modèle itératif.")
        
    lats = df_demandes['lat'].values
    lons = df_demandes['lon'].values
    demandes = df_demandes['demande'].values
    tarifs = df_demandes['tarif_transport'].values
    
    # 1. Initialisation : Barycentre pondéré simple
    poids_demande = demandes.sum()
    if poids_demande == 0:
        raise ValueError("La demande totale ne peut pas être nulle.")
        
    x_current = (lons * demandes).sum() / poids_demande
    y_current = (lats * demandes).sum() / poids_demande
    
    # 2. Modèle de Gravité Itératif
    tolerance = 1e-6
    max_iter = 100
    
    for _ in range(max_iter):
        x_prev, y_prev = x_current, y_current
        
        # Calculer les distances du point courant vers toutes les cibles
        distances = calculer_distances_haversine_vectorise(
            lats, lons, 
            np.full(len(lats), y_current), np.full(len(lons), x_current)
        )
        
        # Gérer la division par zéro (epsilon)
        distances = np.where(distances == 0, 1e-6, distances)
        
        # Calcul des poids ajustés: W_n = (D_n * F_n) / d_n  (Equation académique)
        w_n = (demandes * tarifs) / distances
        w_total = w_n.sum()
        
        if w_total == 0:
            break
            
        # Nouvelles coordonnées : moyennes pondérées
        x_current = (w_n * lons).sum() / w_total
        y_current = (w_n * lats).sum() / w_total
        
        # Test de convergence
        if abs(x_current - x_prev) < tolerance and abs(y_current - y_prev) < tolerance:
            break
            
    lat_optimal, lon_optimal = y_current, x_current
    
    # 3. Calculs finaux pour le reporting
    distances_finales = calculer_distances_haversine_vectorise(
        lats, lons, 
        np.full(len(lats), lat_optimal), np.full(len(lons), lon_optimal)
    )
    df_demandes['distance_au_centre_km'] = distances_finales
    df_demandes['cout_transport_total'] = distances_finales * demandes * tarifs

    return {
        "coordonnees_optimales": (lat_optimal, lon_optimal),
        "distance_moyenne_km": distances_finales.mean(),
        "cout_transport_global": df_demandes['cout_transport_total'].sum(),
        "details_df": df_demandes
    }
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
            d = calculer_distances_haversine_vectorise(trajet['lat'], trajet['lon'], ent['lat'], ent['lon'])
            
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

def haversine(lat1, lon1, lat2, lon2):
    """Calcule la distance Haversine entre deux points (en km)."""
    R = 6371.0
    lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
    lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    return R * c

def calculer_score_mixte(distance, temp, hum, poids):
    """Calcule un score pondéré combinant distance, température et humidité."""
    # Convertit la distance en score (plus la distance est faible, plus le score est élevé. Max 100)
    score_dist = max(0, 100 - (distance * 0.1))
    
    # On calcule la moyenne pondérée
    score = (score_dist * poids.get('dist', 0.5)) + \
            (temp * poids.get('temp', 0.3)) + \
            (hum * poids.get('hum', 0.2))
            
    return round(score, 2)
