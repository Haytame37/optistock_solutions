import pandas as pd
import numpy as np

# ══════════════════════════════════════════════════════════════════════════════
#  SEUILS DE CONFORMITÉ LOGISTIQUE PAR TYPE DE STOCKAGE
#  Référence : Normes HACCP / GDP (Good Distribution Practice)
# ══════════════════════════════════════════════════════════════════════════════

SEUILS_CONFORMITE = {
    "froid": {
        "temp_min": 2.0,   "temp_max": 8.0,    # Chaîne du froid pharmaceutique/alimentaire
        "hum_min": 65.0,   "hum_max": 95.0,
        "temp_ideale": 4.0, "hum_ideale": 80.0,
    },
    "sec": {
        "temp_min": 15.0,  "temp_max": 30.0,    # Stockage ambiant contrôlé
        "hum_min": 30.0,   "hum_max": 60.0,
        "temp_ideale": 22.0, "hum_ideale": 45.0,
    },
    "mixte": {
        "temp_min": 5.0,   "temp_max": 25.0,    # Zone polyvalente
        "hum_min": 40.0,   "hum_max": 80.0,
        "temp_ideale": 15.0, "hum_ideale": 60.0,
    },
}

# Distance de référence pour la normalisation (km)
# Correspond à la plus grande distance logistique courante au Maroc (Tanger → Dakhla ≈ 1800 km)
DISTANCE_REF_KM = 1500.0


def calculer_distances_haversine_vectorise(lat1, lon1, lat2, lon2):
    """
    Calcule la distance Haversine de manière vectorisée avec NumPy.
    Idéal pour traiter des DataFrames complets sans utiliser de boucles.
    
    Arguments:
    lat1, lon1 : Séries Pandas ou tableaux NumPy (ex: Coordonnées des livraisons)
    lat2, lon2 : Séries Pandas ou tableaux NumPy (ex: Coordonnées de l'entrepôt)

    Retourne:
    la distance entre les deux points en km
    """
    R = 6371.0  # Rayon moyen de la Terre en kilomètres

    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = np.sin(dlat / 2.0)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return R * c


def haversine(lat1, lon1, lat2, lon2):
    """Calcule la distance Haversine entre deux points (en km). Version scalaire."""
    R = 6371.0
    lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
    lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    return R * c


# ══════════════════════════════════════════════════════════════════════════════
#  SCORING — NORMALISATION & CONFORMITÉ
# ══════════════════════════════════════════════════════════════════════════════

def score_distance(distance_km, d_ref=DISTANCE_REF_KM):
    """
    Convertit une distance en score [0, 100] via décroissance exponentielle douce.
    Formule : S = 100 × exp(-d / d_ref)
    
    Avantages par rapport à l'ancien modèle linéaire :
    - Aucun entrepôt n'est éliminé brutalement (score > 0 même à 2000 km)
    - Forte pénalité pour les courtes distances qui augmentent (zone 0-500 km)
    - Pente plus douce au-delà (diminishing returns logistique)
    
    | Distance | Ancien score | Nouveau score |
    |----------|-------------|---------------|
    | 0 km     | 100         | 100           |
    | 100 km   | 90          | 93.6          |
    | 500 km   | 50          | 71.7          |
    | 1000 km  | 0 ❌        | 51.3 ✅       |
    | 1500 km  | 0 ❌        | 36.8 ✅       |
    """
    return round(100 * np.exp(-distance_km / d_ref), 2)


def score_conformite_temperature(temp_moyenne, type_stockage):
    """
    Calcule un score de conformité thermique [0, 100] adapté au type de stockage.
    
    Logique : Plus la température moyenne est proche de la valeur idéale
    pour le type de stockage, plus le score est élevé.
    
    - Dans la plage [min, max] → score entre 50 et 100 (proportionnel à la proximité de l'idéale)
    - Hors plage → score entre 0 et 50 (pénalité proportionnelle à l'écart)
    """
    seuils = SEUILS_CONFORMITE.get(type_stockage, SEUILS_CONFORMITE["mixte"])
    t_min, t_max = seuils["temp_min"], seuils["temp_max"]
    t_ideale = seuils["temp_ideale"]
    
    if t_min <= temp_moyenne <= t_max:
        # Dans la plage → score 50-100
        ecart = abs(temp_moyenne - t_ideale)
        amplitude = max(t_ideale - t_min, t_max - t_ideale)
        if amplitude == 0:
            return 100.0
        score = 100 - (ecart / amplitude) * 50
        return round(max(50, score), 2)
    else:
        # Hors plage → score 0-50
        if temp_moyenne < t_min:
            ecart = t_min - temp_moyenne
        else:
            ecart = temp_moyenne - t_max
        # Pénalité : chaque degré hors plage coûte ~5 points
        score = max(0, 50 - ecart * 5)
        return round(score, 2)


def score_conformite_humidite(hum_moyenne, type_stockage):
    """
    Calcule un score de conformité humidité [0, 100] adapté au type de stockage.
    Même logique que la température.
    """
    seuils = SEUILS_CONFORMITE.get(type_stockage, SEUILS_CONFORMITE["mixte"])
    h_min, h_max = seuils["hum_min"], seuils["hum_max"]
    h_ideale = seuils["hum_ideale"]
    
    if h_min <= hum_moyenne <= h_max:
        ecart = abs(hum_moyenne - h_ideale)
        amplitude = max(h_ideale - h_min, h_max - h_ideale)
        if amplitude == 0:
            return 100.0
        score = 100 - (ecart / amplitude) * 50
        return round(max(50, score), 2)
    else:
        if hum_moyenne < h_min:
            ecart = h_min - hum_moyenne
        else:
            ecart = hum_moyenne - h_max
        score = max(0, 50 - ecart * 2)
        return round(score, 2)


def calculer_taux_conformite_iot(df_iot_entrepot, type_stockage):
    """
    Calcule les métriques de conformité IoT à partir des relevés bruts d'un entrepôt.
    
    Retourne un dictionnaire avec :
    - score_temp : Score de conformité température [0, 100]
    - score_hum  : Score de conformité humidité [0, 100]
    - taux_conf  : % de relevés dans les seuils acceptables
    - temp_moy   : Température moyenne (pour affichage)
    - hum_moy    : Humidité moyenne (pour affichage)
    """
    seuils = SEUILS_CONFORMITE.get(type_stockage, SEUILS_CONFORMITE["mixte"])
    
    temp_moy = df_iot_entrepot['temperature'].mean()
    hum_moy = df_iot_entrepot['humidite'].mean()
    
    # Taux de conformité = % de relevés dans la plage acceptable
    conforme_temp = (
        (df_iot_entrepot['temperature'] >= seuils['temp_min']) & 
        (df_iot_entrepot['temperature'] <= seuils['temp_max'])
    ).mean() * 100
    
    conforme_hum = (
        (df_iot_entrepot['humidite'] >= seuils['hum_min']) & 
        (df_iot_entrepot['humidite'] <= seuils['hum_max'])
    ).mean() * 100
    
    # Score combiné : pondération taux_conformité (60%) + proximité_ideale (40%)
    score_temp = round(conforme_temp * 0.6 + score_conformite_temperature(temp_moy, type_stockage) * 0.4, 2)
    score_hum = round(conforme_hum * 0.6 + score_conformite_humidite(hum_moy, type_stockage) * 0.4, 2)
    taux_global = round((conforme_temp + conforme_hum) / 2, 2)
    
    return {
        "score_temp": score_temp,
        "score_hum": score_hum,
        "taux_conf": taux_global,
        "temp_moy": round(temp_moy, 2),
        "hum_moy": round(hum_moy, 2),
    }


def calculer_score_mixte(distance, score_temp, score_hum, poids, score_capacite=100):
    """
    Calcule le score final pondéré. 
    TOUS les composants sont maintenant normalisés sur [0, 100].
    
    Formule : S = Σ(Ci × Wi) avec Ci ∈ [0, 100] et ΣWi = 1
    
    Arguments :
    - distance    : Distance en km (sera convertie en score via score_distance)
    - score_temp  : Score conformité temp [0,100] (déjà normalisé)
    - score_hum   : Score conformité hum [0,100] (déjà normalisé)
    - poids       : Dict {'dist': float, 'temp': float, 'hum': float}
    - score_capacite : Score de capacité [0,100] (100 = largement disponible)
    """
    s_dist = score_distance(distance)
    
    score = (s_dist * poids.get('dist', 0.5)) + \
            (score_temp * poids.get('temp', 0.3)) + \
            (score_hum * poids.get('hum', 0.2))
    
    return round(score, 2)


def compatibilite_type_stockage(type_entrepot, type_requis):
    """
    Évalue la compatibilité entre le type d'entrepôt et le besoin client.
    
    Retourne un coefficient multiplicateur :
    - 1.0  : Correspondance exacte
    - 0.85 : Entrepôt mixte pour un besoin spécifique (capable mais moins spécialisé)
    - 0.0  : Incompatible (ex: entrepôt sec pour besoin froid)
    """
    if type_entrepot == type_requis:
        return 1.0
    elif type_entrepot == "mixte":
        return 0.85  # Mixte peut servir froid ou sec, avec 15% de malus
    elif type_requis == "mixte":
        return 0.90  # Besoin mixte, entrepôt spécialisé = légèrement sur-qualifié
    else:
        return 0.0   # Incompatible (froid ≠ sec)


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 2 : CENTRE DE GRAVITÉ ITÉRATIF (Weber)
# ══════════════════════════════════════════════════════════════════════════════

def analyser_demandes_et_localiser(df_demandes):
    """
    Calcule le centre de stockage optimal en minimisant le coût total de transport
    via le modèle de gravité itératif (Algorithme de Weber / Weiszfeld).
    
    Attends un DataFrame avec les colonnes: ['ville', 'lat', 'lon', 'demande', 'tarif_transport']
    
    Coût de transport : CT = Σ (tarif_i × demande_i × distance_i)
    Avec tarif en MAD/unité/km — représente le coût unitaire par km.
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
    
    # 2. Modèle de Gravité Itératif (Weiszfeld)
    tolerance = 1e-6
    max_iter = 200
    alpha = 0.8  # Facteur de relaxation pour éviter les oscillations
    
    for iteration in range(max_iter):
        x_prev, y_prev = x_current, y_current
        
        # Calculer les distances du point courant vers toutes les cibles
        distances = calculer_distances_haversine_vectorise(
            lats, lons, 
            np.full(len(lats), y_current), np.full(len(lons), x_current)
        )
        
        # Gérer la division par zéro (epsilon)
        distances = np.where(distances == 0, 1e-6, distances)
        
        # Poids ajustés : W_n = (D_n × F_n) / d_n
        w_n = (demandes * tarifs) / distances
        w_total = w_n.sum()
        
        if w_total == 0:
            break
            
        # Nouvelles coordonnées : moyennes pondérées avec relaxation
        x_new = (w_n * lons).sum() / w_total
        y_new = (w_n * lats).sum() / w_total
        
        # Relaxation pour stabiliser la convergence
        x_current = alpha * x_new + (1 - alpha) * x_prev
        y_current = alpha * y_new + (1 - alpha) * y_prev
        
        # Test de convergence
        if abs(x_current - x_prev) < tolerance and abs(y_current - y_prev) < tolerance:
            break
            
    lat_optimal, lon_optimal = y_current, x_current
    
    # 3. Calculs finaux pour le reporting
    distances_finales = calculer_distances_haversine_vectorise(
        lats, lons, 
        np.full(len(lats), lat_optimal), np.full(len(lons), lon_optimal)
    )
    df_demandes = df_demandes.copy()  # Éviter le SettingWithCopyWarning
    df_demandes['distance_au_centre_km'] = distances_finales.round(2)
    
    # Coût de transport : CT_i = tarif_i × demande_i × distance_i
    # Interprétation : tarif_transport = coût par unité de demande par km
    df_demandes['cout_transport'] = (distances_finales * demandes * tarifs).round(2)

    return {
        "coordonnees_optimales": (lat_optimal, lon_optimal),
        "distance_moyenne_km": round(distances_finales.mean(), 2),
        "cout_transport_global": df_demandes['cout_transport'].sum(),
        "details_df": df_demandes
    }


def calculer_centre_gravite(points_livraison):
    """
    Calcule le point optimal (Lat, Lon) pour une nouvelle implantation.
    points_livraison: Liste de dictionnaires [{'lat': float, 'lon': float, 'volume': float}]
    """
    total_volume = sum(p['volume'] for p in points_livraison)
    
    if total_volume == 0:
        return None, None

    lat_optimal = sum(p['lat'] * p['volume'] for p in points_livraison) / total_volume
    lon_optimal = sum(p['lon'] * p['volume'] for p in points_livraison) / total_volume
    return round(lat_optimal, 4), round(lon_optimal, 4)


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 2 ÉTENDU : IMPLANTATION MULTI-ENTREPÔTS (K-Means + Weber)
# ══════════════════════════════════════════════════════════════════════════════

def _kmeans_geo(lats, lons, demandes, n_clusters, max_iter=100):
    """
    K-Means géographique pondéré par la demande.
    Partitionne les points de demande en N zones cohérentes.
    
    Retourne : labels (array d'affectation cluster pour chaque point)
    """
    n = len(lats)
    
    # Initialisation : choisir N centres parmi les points existants (K-Means++ simplifié)
    indices = list(range(n))
    centers_idx = [indices.pop(np.random.randint(len(indices)))]
    
    for _ in range(1, n_clusters):
        dists = np.array([
            min(haversine(lats[i], lons[i], lats[c], lons[c]) for c in centers_idx)
            for i in indices
        ])
        # Pondérer par distance² × demande pour disperser
        weights = (dists ** 2) * np.array([demandes[i] for i in indices])
        if weights.sum() == 0:
            weights = np.ones(len(weights))
        weights = weights / weights.sum()
        chosen = np.random.choice(len(indices), p=weights)
        centers_idx.append(indices.pop(chosen))
    
    # Coordonnées des centres
    center_lats = np.array([lats[i] for i in centers_idx], dtype=float)
    center_lons = np.array([lons[i] for i in centers_idx], dtype=float)
    
    labels = np.zeros(n, dtype=int)
    
    for iteration in range(max_iter):
        # Affectation : chaque point au centre le plus proche
        new_labels = np.zeros(n, dtype=int)
        for i in range(n):
            dists_to_centers = [
                haversine(lats[i], lons[i], center_lats[k], center_lons[k])
                for k in range(n_clusters)
            ]
            new_labels[i] = int(np.argmin(dists_to_centers))
        
        # Mise à jour des centres (barycentre pondéré par demande)
        new_center_lats = np.zeros(n_clusters)
        new_center_lons = np.zeros(n_clusters)
        
        for k in range(n_clusters):
            mask = new_labels == k
            if mask.sum() == 0:
                new_center_lats[k] = center_lats[k]
                new_center_lons[k] = center_lons[k]
                continue
            w = demandes[mask]
            w_sum = w.sum()
            if w_sum == 0:
                w_sum = 1
            new_center_lats[k] = (lats[mask] * w).sum() / w_sum
            new_center_lons[k] = (lons[mask] * w).sum() / w_sum
        
        # Convergence ?
        if np.array_equal(new_labels, labels):
            break
        
        labels = new_labels
        center_lats = new_center_lats
        center_lons = new_center_lons
    
    return labels, center_lats, center_lons


def analyser_multi_entrepots(df_demandes, n_entrepots=2):
    """
    Calcule N emplacements optimaux pour des entrepôts via K-Means + Weber itératif.
    
    Algorithme :
    1. K-Means géographique pondéré → partition en N zones
    2. Weber/Weiszfeld par zone → centre optimal de chaque zone
    3. Calcul des KPIs par zone et global
    
    Retourne un dictionnaire avec les résultats par zone et globaux.
    """
    lats = df_demandes['lat'].values.astype(float)
    lons = df_demandes['lon'].values.astype(float)
    demandes = df_demandes['demande'].values.astype(float)
    tarifs = df_demandes['tarif_transport'].values.astype(float)
    
    if n_entrepots == 1:
        # Cas simple : un seul entrepôt → Weber classique
        result = analyser_demandes_et_localiser(df_demandes)
        result['zones'] = [{
            'zone_id': 1,
            'coordonnees': result['coordonnees_optimales'],
            'nb_clients': len(df_demandes),
            'cout_transport': result['cout_transport_global'],
            'df': result['details_df'],
        }]
        return result
    
    # 1. K-Means géographique
    np.random.seed(42)
    labels, _, _ = _kmeans_geo(lats, lons, demandes, n_entrepots)
    
    df_demandes = df_demandes.copy()
    df_demandes['zone'] = labels
    
    # 2. Weber par zone
    zones_results = []
    all_dfs = []
    
    for zone_id in range(n_entrepots):
        df_zone = df_demandes[df_demandes['zone'] == zone_id].copy()
        
        if len(df_zone) == 0:
            continue
        
        # Sous-ensemble pour Weber
        df_weber = df_zone[['ville', 'lat', 'lon', 'demande', 'tarif_transport']].copy()
        
        try:
            zone_result = analyser_demandes_et_localiser(df_weber)
        except ValueError:
            continue
        
        zone_df = zone_result['details_df'].copy()
        zone_df['zone'] = zone_id + 1
        all_dfs.append(zone_df)
        
        zones_results.append({
            'zone_id': zone_id + 1,
            'coordonnees': zone_result['coordonnees_optimales'],
            'nb_clients': len(df_zone),
            'cout_transport': zone_result['cout_transport_global'],
            'distance_moy': zone_result['distance_moyenne_km'],
            'df': zone_df,
        })
    
    # 3. Résultats globaux
    details_global = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    cout_global = sum(z['cout_transport'] for z in zones_results)
    
    coords_list = [z['coordonnees'] for z in zones_results]
    
    return {
        'coordonnees_optimales': coords_list,
        'cout_transport_global': cout_global,
        'distance_moyenne_km': details_global['distance_au_centre_km'].mean() if not details_global.empty else 0,
        'details_df': details_global,
        'zones': zones_results,
        'n_entrepots': len(zones_results),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 1 ÉTENDU : CLUSTERING CLIENTS POUR RECOMMANDATION MULTI-ENTREPÔTS
# ══════════════════════════════════════════════════════════════════════════════

def clustering_clients_pour_recommandation(df_trajets, n_zones):
    """
    Répartit les clients en N zones géographiques cohérentes via K-Means.
    Chaque zone recevra ensuite sa propre recommandation d'entrepôt.
    
    Retourne : df_trajets avec une colonne 'zone' ajoutée
    """
    lats = df_trajets['lat'].values.astype(float)
    lons = df_trajets['lon'].values.astype(float)
    poids_uniformes = np.ones(len(lats))
    
    np.random.seed(42)
    labels, center_lats, center_lons = _kmeans_geo(lats, lons, poids_uniformes, n_zones)
    
    df_result = df_trajets.copy()
    df_result['zone'] = labels + 1  # 1-indexed
    
    return df_result, center_lats, center_lons

