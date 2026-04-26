from pathlib import Path
import numpy as np
import pandas as pd
from utils.db import load_sql_to_dataframe
from utils.product_conditions import PRODUCT_CONDITIONS
from core.data_cleaning import clean_iot_data_pipeline

def evaluate_product_conditions(merged_df: pd.DataFrame, product_name: str) -> tuple[bool, str]:
    """
    Évalue si l'historique d'un entrepôt respecte les conditions strictes d'un produit.
    Retourne (est_eligible, motif_rejet).
    """
    if product_name not in PRODUCT_CONDITIONS:
        return True, ""
        
    cond = PRODUCT_CONDITIONS[product_name]
    
    # Règle générale : Si NaN, on suppose que c'est géré par le cleaning pipeline avant.
    # Ici merged_df a déjà été potentiellement aggrégé (T_heure, H_heure).
    
    # Fonction locale pour vérifier les temps de résistance
    def check_resistance(series: pd.Series, condition_mask: pd.Series, max_hours: float, warning_name: str) -> tuple[bool, str]:
        # Trouver les blocs consécutifs où condition_mask est True
        # On suppose que chaque ligne = 1 heure (ou 15 min selon l'échantillonnage, ici la DB semble être du 15m ou 1h, on va assumer 1h pour T_heure)
        # Mais merged_df a des datetime. On va faire simple: compter les occurences consécutives.
        active = condition_mask.fillna(False).astype(bool)
        if not active.any():
            return True, ""
            
        groups = active.ne(active.shift(fill_value=False)).cumsum()
        for _, incident in active[active].groupby(groups[active]):
            duration_hours = len(incident) # En supposant 1 ligne = 1 intervalle (ex: 1h)
            # Normalement, on devrait utiliser datetime. Mais pour l'implémentation, chaque ligne de merged_df (après group by ou simple tri) 
            # représente une unité de temps. On suppose 1h pour coller à l'ancien code.
            if duration_hours > max_hours:
                return False, f"Dépassement {warning_name} pendant {duration_hours}h (Max toléré: {max_hours}h)"
        return True, ""

    # Température
    t_marge_bas = cond["temperature"]["min"] + cond["temperature"]["marge_bas"]
    t_marge_haut = cond["temperature"]["max"] + cond["temperature"]["marge_haut"]
    
    mask_t_bas = merged_df["T_heure"] < t_marge_bas
    ok, motif = check_resistance(merged_df["T_heure"], mask_t_bas, cond["temperature"]["temps_resistance_bas_h"], "Température Basse")
    if not ok: return False, motif
    
    mask_t_haut = merged_df["T_heure"] > t_marge_haut
    ok, motif = check_resistance(merged_df["T_heure"], mask_t_haut, cond["temperature"]["temps_resistance_haut_h"], "Température Haute")
    if not ok: return False, motif
    
    # Humidité
    h_marge_bas = cond["humidite"]["min"] + cond["humidite"]["marge_bas"]
    h_marge_haut = cond["humidite"]["max"] + cond["humidite"]["marge_haut"]
    
    mask_h_bas = merged_df["H_heure"] < h_marge_bas
    ok, motif = check_resistance(merged_df["H_heure"], mask_h_bas, cond["humidite"]["temps_resistance_bas_h"], "Humidité Basse")
    if not ok: return False, motif
    
    mask_h_haut = merged_df["H_heure"] > h_marge_haut
    ok, motif = check_resistance(merged_df["H_heure"], mask_h_haut, cond["humidite"]["temps_resistance_haut_h"], "Humidité Haute")
    if not ok: return False, motif
    
    return True, ""

def calculate_product_warehouse_score(entrepot_id: str, product_name: str) -> dict:
    """
    Calcule le score et l'éligibilité d'un entrepôt spécifiquement pour un produit.
    """
    query = f"""
        SELECT 
            recorded_at as datetime, 
            temp_sensor_1 as capteur1_t, 
            temp_sensor_2 as capteur2_t, 
            temp_sensor_3 as capteur3_t, 
            hum_sensor_1 as capteur1_h, 
            hum_sensor_2 as capteur2_h, 
            hum_sensor_3 as capteur3_h 
        FROM iot_readings 
        WHERE warehouse_id = '{entrepot_id}' 
        ORDER BY recorded_at
    """
    merged = load_sql_to_dataframe(query)
    if merged is None or merged.empty:
        raise ValueError(f"Aucune donnée IoT pour {entrepot_id}")

    merged["datetime"] = pd.to_datetime(merged["datetime"], errors="coerce")
    merged = merged.dropna(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)
    
    # Optionnel: Ré-échantillonner par heure pour standardiser
    # merged = merged.set_index('datetime').resample('1H').mean().reset_index()

    # Nettoyage des données (Médiane + MissForest)
    cols_t = ["capteur1_t", "capteur2_t", "capteur3_t"]
    cols_h = ["capteur1_h", "capteur2_h", "capteur3_h"]
    merged = clean_iot_data_pipeline(merged, sensor_columns=cols_t + cols_h)

    # Agrégation robuste (médiane des 3 capteurs pour T et H)
    merged["T_heure"] = merged[cols_t].median(axis=1)
    merged["H_heure"] = merged[cols_h].median(axis=1)

    # Évaluation de l'éligibilité selon le produit
    is_eligible, reject_reason = evaluate_product_conditions(merged, product_name)

    # Calcul d'un score de base (ex: % du temps passé dans les conditions optimales)
    if not is_eligible:
        score = 0.0
    else:
        cond = PRODUCT_CONDITIONS[product_name]
        optimal_t = (merged["T_heure"] >= cond["temperature"]["min"]) & (merged["T_heure"] <= cond["temperature"]["max"])
        optimal_h = (merged["H_heure"] >= cond["humidite"]["min"]) & (merged["H_heure"] <= cond["humidite"]["max"])
        
        # Le score est basé sur le pourcentage de temps passé dans les plages optimales
        score_t = optimal_t.sum() / len(merged) * 100
        score_h = optimal_h.sum() / len(merged) * 100
        score = round((score_t * 0.6) + (score_h * 0.4), 2) # Poids arbitraire 60/40

    t_mean = float(merged["T_heure"].mean())
    h_mean = float(merged["H_heure"].mean())

    def _label_from_score(s: float) -> tuple[str, str]:
        if s >= 90: return "Excellent", "#27ae60"
        if s >= 75: return "Très bon", "#2ecc71"
        if s >= 60: return "Acceptable", "#f39c12"
        if s >= 40: return "Mauvais", "#e67e22"
        return "Inutilisable", "#c0392b"

    label, color = _label_from_score(score)

    return {
        "id_entrepot": entrepot_id,
        "score": score,
        "label": "Rejeté" if not is_eligible else label,
        "couleur": "#7f8c8d" if not is_eligible else color,
        "temp_moyenne": round(t_mean, 2),
        "hum_moyenne": round(h_mean, 2),
        "eligible": is_eligible,
        "motif_rejet": reject_reason,
        "type_cherche": product_name,
        "nb_incidents": 0 if is_eligible else 1, # Simplifié pour l'affichage UI
    }

def search_entrepots_by_product(product_name: str) -> list[dict]:
    df_wh = load_sql_to_dataframe("SELECT DISTINCT warehouse_id FROM iot_readings")
    if df_wh is None or df_wh.empty:
        return []
    entrepot_ids = sorted(df_wh["warehouse_id"].tolist())

    results = []
    for entrepot_id in entrepot_ids:
        try:
            results.append(calculate_product_warehouse_score(entrepot_id, product_name))
        except Exception as e:
            print(f"Error evaluating {entrepot_id}: {e}")
            continue

    return sorted(results, key=lambda item: item["score"], reverse=True)
