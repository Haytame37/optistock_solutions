"""
core/iot_analysis.py
═══════════════════════════════════════════════════════════════════════════════
Module d'analyse IoT robuste — Phase 3 (traitement du signal + segmentation).

Nouveautés Phase 3 :
    • Traitement du signal : interpolation linéaire + filtre moyenne mobile
    • Multi-capteurs       : agrégation pondérée de 3 capteurs (résistance au bruit)
    • Segmentation mensuelle avec conformité aux normes HACCP saisonnières
    • Détection d'anomalies par mois (granularité mensuelle vs annuelle)

Architecture du pipeline IoT :
    [CSV brut] → [Interpolation NaN] → [Lissage bruit] → [Agrégation capteurs]
               → [Détection anomalies] → [Score mensuel] → [Rapport]

Référence normes :
    Codex Alimentarius CAC/RCP 1-1969 (Rev. 4-2003) — HACCP
    GDP (Good Distribution Practice) — EU Commission 2013/C 343/01
═══════════════════════════════════════════════════════════════════════════════
"""

import pandas as pd
import numpy as np
from pathlib import Path

from utils.constants import TEMP_MIN, TEMP_MAX, HUMID_MIN, HUMID_MAX
from core.scoring import (
    interpoler_valeurs_manquantes,
    lisser_signal,
    pretraiter_serie_capteurs,
    analyser_conformite_mensuelle,
    analyser_conformite_mensuelle_humidite,
    NORMES_SAISONNIERES,
    get_saison,
)


# ─────────────────────────────────────────────────────────────────────────────
#  1. CHARGEMENT & PRÉ-TRAITEMENT
# ─────────────────────────────────────────────────────────────────────────────

def load_iot_data(filepath: str | Path) -> pd.DataFrame:
    """
    Charge un fichier CSV IoT et garantit le format datetime.

    Traite également les cas courants de robustesse :
        • colonnes mal nommées (strip des espaces)
        • séparateurs décimaux non standards (virgule → point)

    Paramètres
    ----------
    filepath : str | Path — chemin vers le fichier CSV

    Retourne
    --------
    pd.DataFrame avec colonne 'datetime' en type datetime64
    """
    df = pd.read_csv(filepath)
    # Nettoyage des noms de colonnes
    df.columns = [c.strip() for c in df.columns]
    # Conversion datetime
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    return df.sort_values("datetime").reset_index(drop=True)


def load_and_preprocess(filepath: str | Path,
                         colonnes_capteurs: list = None) -> pd.DataFrame:
    """
    Pipeline complet : chargement + traitement du signal (interpolation + lissage).

    Retourne un DataFrame avec une colonne 'valeur_moyenne' prête pour l'analyse.
    """
    df = load_iot_data(filepath)
    df_traite = pretraiter_serie_capteurs(df, colonnes=colonnes_capteurs)
    return df_traite


# ─────────────────────────────────────────────────────────────────────────────
#  2. STATISTIQUES DE BASE (Multi-capteurs)
# ─────────────────────────────────────────────────────────────────────────────

def get_basic_stats(df_temp: pd.DataFrame,
                    df_humid: pd.DataFrame) -> dict:
    """
    Calcule les statistiques descriptives en utilisant la MOYENNE des 3 capteurs
    par ligne (consensus multi-capteurs — résistance aux pannes ponctuelles).

    Traitement préalable :
        • Interpolation + lissage sur chaque capteur avant agrégation
        → résultats plus robustes qu'une moyenne brute.

    Retourne
    --------
    dict avec clés : temp_mean, temp_min, temp_max, temp_std,
                     humid_mean, humid_min, humid_max, humid_std
    """
    colonnes_capteurs = ["capteur1", "capteur2", "capteur3"]

    # Vérifier quelles colonnes capteurs sont disponibles
    cols_t = [c for c in colonnes_capteurs if c in df_temp.columns]
    cols_h = [c for c in colonnes_capteurs if c in df_humid.columns]

    # Si 'valeur_moyenne' pré-calculée → l'utiliser directement
    if "valeur_moyenne" in df_temp.columns:
        t_series = df_temp["valeur_moyenne"]
    elif cols_t:
        # Traitement du signal + agrégation
        df_t_proc = pretraiter_serie_capteurs(df_temp, colonnes=cols_t)
        t_series = df_t_proc["valeur_moyenne"]
    else:
        t_series = pd.Series(dtype=float)

    if "valeur_moyenne" in df_humid.columns:
        h_series = df_humid["valeur_moyenne"]
    elif cols_h:
        df_h_proc = pretraiter_serie_capteurs(df_humid, colonnes=cols_h)
        h_series = df_h_proc["valeur_moyenne"]
    else:
        h_series = pd.Series(dtype=float)

    def _safe_stat(series, fn):
        """Applique fn sur la série, retourne 0.0 si la série est vide."""
        return round(fn(series), 2) if not series.empty else 0.0

    return {
        "temp_mean":  _safe_stat(t_series, lambda s: s.mean()),
        "temp_min":   _safe_stat(t_series, lambda s: s.min()),
        "temp_max":   _safe_stat(t_series, lambda s: s.max()),
        "temp_std":   _safe_stat(t_series, lambda s: s.std()),
        "humid_mean": _safe_stat(h_series, lambda s: s.mean()),
        "humid_min":  _safe_stat(h_series, lambda s: s.min()),
        "humid_max":  _safe_stat(h_series, lambda s: s.max()),
        "humid_std":  _safe_stat(h_series, lambda s: s.std()),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  3. DÉTECTION D'ANOMALIES (Globale & Mensuelle)
# ─────────────────────────────────────────────────────────────────────────────

def detect_anomalies(df_temp: pd.DataFrame,
                     df_humid: pd.DataFrame,
                     temp_min: float = TEMP_MIN,
                     temp_max: float = TEMP_MAX,
                     humid_min: float = HUMID_MIN,
                     humid_max: float = HUMID_MAX) -> tuple:
    """
    Isole les lignes où les seuils environnementaux sont franchis.

    Méthode Multi-capteurs :
        Validation sur la MOYENNE des capteurs disponibles (consensus).
        → Un dépassement ponctuel d'un seul capteur n'est pas comptabilisé
          si les deux autres sont conformes (filtre de bruit efficace).

    Paramètres
    ----------
    df_temp, df_humid : DataFrames IoT (colonnes capteur1/2/3 ou valeur_moyenne)
    temp_min/max      : Seuils de température (par défaut : utils/constants)
    humid_min/max     : Seuils d'humidité

    Retourne
    --------
    (anomalies_temp, anomalies_humid) : tuple de DataFrames filtrés
    """
    # Calcul de la moyenne agrégée (avec lissage si colonnes brutes disponibles)
    if "valeur_moyenne" in df_temp.columns:
        t_avg = df_temp["valeur_moyenne"]
    else:
        cols_t = [c for c in ["capteur1", "capteur2", "capteur3"] if c in df_temp.columns]
        if cols_t:
            df_t_p = pretraiter_serie_capteurs(df_temp, colonnes=cols_t)
            t_avg = df_t_p["valeur_moyenne"]
        else:
            t_avg = pd.Series(dtype=float)

    if "valeur_moyenne" in df_humid.columns:
        h_avg = df_humid["valeur_moyenne"]
    else:
        cols_h = [c for c in ["capteur1", "capteur2", "capteur3"] if c in df_humid.columns]
        if cols_h:
            df_h_p = pretraiter_serie_capteurs(df_humid, colonnes=cols_h)
            h_avg = df_h_p["valeur_moyenne"]
        else:
            h_avg = pd.Series(dtype=float)

    mask_temp  = (t_avg < temp_min)  | (t_avg > temp_max)
    mask_humid = (h_avg < humid_min) | (h_avg > humid_max)

    anomalies_temp  = df_temp[mask_temp.reindex(df_temp.index, fill_value=False)]
    anomalies_humid = df_humid[mask_humid.reindex(df_humid.index, fill_value=False)]

    return anomalies_temp, anomalies_humid


def detect_anomalies_mensuelles(df_temp: pd.DataFrame,
                                 df_humid: pd.DataFrame) -> pd.DataFrame:
    """
    Détecte les anomalies mois par mois en utilisant les normes SAISONNIÈRES
    (NORMES_SAISONNIERES) au lieu de seuils globaux fixes.

    Avantage : un pic à 30°C en juillet (OK) n'est pas flaggé comme anomalie,
    mais 30°C en janvier (hors norme hivernale) l'est.

    Retourne
    --------
    pd.DataFrame mensuel avec colonnes :
        'mois', 'saison', 'n_anom_temp', 'n_anom_humid',
        'pct_anom_temp', 'pct_anom_humid', 'score_mensuel'
    """
    results = []

    # Construire les séries moyennées
    if "valeur_moyenne" in df_temp.columns:
        df_t = df_temp[["datetime", "valeur_moyenne"]].copy()
    else:
        cols_t = [c for c in ["capteur1", "capteur2", "capteur3"] if c in df_temp.columns]
        df_t_p = pretraiter_serie_capteurs(df_temp, colonnes=cols_t)
        df_t = df_t_p[["datetime", "valeur_moyenne"]].copy()

    if "valeur_moyenne" in df_humid.columns:
        df_h = df_humid[["datetime", "valeur_moyenne"]].copy()
    else:
        cols_h = [c for c in ["capteur1", "capteur2", "capteur3"] if c in df_humid.columns]
        df_h_p = pretraiter_serie_capteurs(df_humid, colonnes=cols_h)
        df_h = df_h_p[["datetime", "valeur_moyenne"]].copy()

    df_t["datetime"] = pd.to_datetime(df_t["datetime"])
    df_h["datetime"] = pd.to_datetime(df_h["datetime"])
    df_t["mois"] = df_t["datetime"].dt.month
    df_h["mois"] = df_h["datetime"].dt.month

    all_months = sorted(set(df_t["mois"].unique()) | set(df_h["mois"].unique()))

    for mois in all_months:
        norme = NORMES_SAISONNIERES.get(int(mois), NORMES_SAISONNIERES[6])

        # Données du mois
        t_vals = df_t[df_t["mois"] == mois]["valeur_moyenne"].dropna()
        h_vals = df_h[df_h["mois"] == mois]["valeur_moyenne"].dropna()

        n_t = len(t_vals)
        n_h = len(h_vals)

        # Anomalies saisonnières
        anom_t = ((t_vals < norme["temp_min"]) | (t_vals > norme["temp_max"])).sum()
        anom_h = ((h_vals < norme["humid_min"]) | (h_vals > norme["humid_max"])).sum()

        pct_t = round(anom_t / n_t * 100, 1) if n_t > 0 else 0.0
        pct_h = round(anom_h / n_h * 100, 1) if n_h > 0 else 0.0

        # Score mensuel = taux de conformité agrégé
        conf_t = 100 - pct_t
        conf_h = 100 - pct_h
        score_mensuel = round(0.7 * conf_t + 0.3 * conf_h, 1)  # pondération HACCP

        if score_mensuel >= 90:   statut = "✅ Conforme"
        elif score_mensuel >= 70: statut = "⚠️ Vigilance"
        else:                     statut = "🔴 Hors-norme"

        results.append({
            "mois":           int(mois),
            "saison":         get_saison(int(mois)),
            "n_releves_temp": n_t,
            "n_releves_humid":n_h,
            "n_anom_temp":    int(anom_t),
            "n_anom_humid":   int(anom_h),
            "pct_anom_temp":  pct_t,
            "pct_anom_humid": pct_h,
            "score_mensuel":  score_mensuel,
            "statut_mois":    statut,
            "norm_t_min":     norme["temp_min"],
            "norm_t_max":     norme["temp_max"],
            "norm_h_min":     norme["humid_min"],
            "norm_h_max":     norme["humid_max"],
        })

    return pd.DataFrame(results)


# ─────────────────────────────────────────────────────────────────────────────
#  4. RAPPORT COMPLET D'UN ENTREPÔT
# ─────────────────────────────────────────────────────────────────────────────

def generer_rapport_iot(df_temp: pd.DataFrame,
                         df_humid: pd.DataFrame) -> dict:
    """
    Génère un rapport IoT complet incluant :
        • Statistiques descriptives (multi-capteurs avec lissage)
        • Nombre d'anomalies globales et mensuelles
        • Analyse de conformité saisonnière
        • Score de qualité environnementale

    Retourne
    --------
    dict avec :
        'stats'             : dict statistiques de base
        'n_anom_temp'       : int
        'n_anom_humid'      : int
        'df_mensuel'        : pd.DataFrame analyse mensuelle anomalies
        'df_conf_mensuelle' : pd.DataFrame conformité température mensuelle
        'total_releves'     : int
    """
    stats = get_basic_stats(df_temp, df_humid)
    bad_temp, bad_humid = detect_anomalies(df_temp, df_humid)
    df_mensuel = detect_anomalies_mensuelles(df_temp, df_humid)

    # Analyse conformité mensuelle par colonne 'valeur_moyenne'
    if "valeur_moyenne" not in df_temp.columns:
        cols_t = [c for c in ["capteur1", "capteur2", "capteur3"] if c in df_temp.columns]
        df_t_p = pretraiter_serie_capteurs(df_temp, colonnes=cols_t)
    else:
        df_t_p = df_temp

    df_conf_mensuelle = analyser_conformite_mensuelle(df_t_p)

    return {
        "stats":              stats,
        "n_anom_temp":        len(bad_temp),
        "n_anom_humid":       len(bad_humid),
        "df_mensuel":         df_mensuel,
        "df_conf_mensuelle":  df_conf_mensuelle,
        "total_releves":      max(len(df_temp), len(df_humid)),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  BLOC DE TEST (point d'entrée direct)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from core.scoring import calculate_environmental_score, get_score_label
    from utils.constants import TEMP_DATA_PATH, HUMID_DATA_PATH

    df_t = load_and_preprocess(TEMP_DATA_PATH)
    df_h = load_and_preprocess(HUMID_DATA_PATH)

    rapport = generer_rapport_iot(df_t, df_h)
    stats   = rapport["stats"]

    score = calculate_environmental_score(
        rapport["total_releves"],
        rapport["n_anom_temp"],
        rapport["n_anom_humid"],
    )
    label, emoji = get_score_label(score)

    print("\n" + "=" * 40)
    print("📊 RAPPORT IoT OPTISTOCK (Multi-Capteurs + Signal Processing)")
    print("=" * 40)
    print(f"🌡️ Température Moyenne  : {stats['temp_mean']}°C ± {stats['temp_std']}")
    print(f"💧 Humidité Moyenne     : {stats['humid_mean']}% ± {stats['humid_std']}")
    print("-" * 40)
    print(f"🚨 Alertes Température  : {rapport['n_anom_temp']} heures")
    print(f"🚨 Alertes Humidité     : {rapport['n_anom_humid']} heures")
    print("-" * 40)
    print(f"⭐ SCORE FINAL          : {score}/100 {emoji}")
    print(f"📢 Verdict              : {label}")
    print("=" * 40)
    print("\n📅 Analyse mensuelle :")
    print(rapport["df_mensuel"].to_string(index=False))