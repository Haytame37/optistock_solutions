import pandas as pd
import numpy as np
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
    Calcule le centre de stockage optimal et évalue les distances.
    Attends un DataFrame avec les colonnes: ['nom', 'lat', 'lon', 'demande']
    """
    # 1. Calcul du Centre de Gravité (Barycentre pondéré)
    poids_total = df_demandes['demande'].sum()
    
    if poids_total == 0:
        raise ValueError("La demande totale ne peut pas être nulle.")

    lat_centre = (df_demandes['lat'] * df_demandes['demande']).sum() / poids_total
    lon_centre = (df_demandes['lon'] * df_demandes['demande']).sum() / poids_total

    # 2. Calcul des distances vectorisées vers le centre optimal
    # Utilisation de la fonction exigée sans la redéfinir
    df_demandes['distance_au_centre_km'] = calculer_distances_haversine_vectorise(
        df_demandes['lat'].values,
        df_demandes['lon'].values,
        np.full(len(df_demandes), lat_centre), # Répète la latitude du centre
        np.full(len(df_demandes), lon_centre)  # Répète la longitude du centre
    )

    # 3. Calcul du "Moment de transport" (Indicateur de coût : Demande * Distance)
    #df_demandes['cout_transport_estime'] = df_demandes['demande'] * df_demandes['distance_au_centre_km']

    return {
        "coordonnees_optimales": (lat_centre, lon_centre),
        "distance_moyenne_km": df_demandes['distance_au_centre_km'].mean(),
        #"cout_transport_global": df_demandes['cout_transport_estime'].sum(),
        "details_df": df_demandes
    }