"""
core/scoring.py
═══════════════════════════════════════════════════════════════════════════════
Module de calcul du score final — Phase 3 & 4 (Fusion SAW 60/40).

Architecture des scores (3 couches) :
    Couche 1 — Données brutes (IoT capteurs, distances Haversine)
    Couche 2 — Normalisation Min-Max [0, 1]
               • Distance  : inverse (1/d) avant normalisation
                 → la PROXIMITÉ est valorisée, pas l'éloignement
               • Score IoT : normalisation classique (x - min) / (max - min)
    Couche 3 — Fusion SAW (Simple Additive Weighting)
               Score_Global = 0.60 × Logistique + 0.40 × Environnement

Justification pondération 60/40 (norme GDP / HACCP) :
    • La logistique (60 %) capture la proximité physique ET la fiabilité temps
      réel des capteurs — facteur directement lié à la rentabilité supply-chain.
    • L'environnement (40 %) mesure la conformité T°/Humidité — critique mais
      améliorable par des équipements (isolation, CVC), d'où un poids moindre.

Traitement du signal (robustesse données) :
    • Interpolation linéaire  : comble les valeurs manquantes (NaN)
    • Filtre moyenne mobile   : lisse le bruit capteur (fenêtre configurable)
    • Multi-capteurs          : moyenne pondérée de 3 capteurs préalable

Référence mathématique :
    Triantaphyllou, E. (2000). Multi-Criteria Decision Making Methods.
    Springer. (SAW — Simple Additive Weighting, pp. 5-6)
═══════════════════════════════════════════════════════════════════════════════
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional

from utils.constants import WEIGHT_TEMP, WEIGHT_HUMID


# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTES SAW
# ─────────────────────────────────────────────────────────────────────────────

# Poids SAW Phase 4 — définis dans le cahier des charges
POIDS_LOGISTIQUE    = 0.60   # 60 % → fiabilité IoT + proximité géographique
POIDS_ENVIRONNEMENT = 0.40   # 40 % → conformité thermique / hygrométrique

# Fallbacks si un axe est manquant (score neutre, ni pénalisant ni avantageux)
SCORE_LOG_DEFAUT = 50.0
SCORE_ENV_DEFAUT = 50.0

# Seuils industriels saisonniers de conformité (réf. HACCP / EN ISO 22000)
# Clé : mois (1-12) → dict {temp_min, temp_max, humid_min, humid_max}
NORMES_SAISONNIERES = {
    # Hiver (déc, jan, fév) — risques : gel, humidité excessive
    12: {"temp_min": 4.0,  "temp_max": 22.0, "humid_min": 35.0, "humid_max": 65.0},
     1: {"temp_min": 4.0,  "temp_max": 22.0, "humid_min": 35.0, "humid_max": 65.0},
     2: {"temp_min": 4.0,  "temp_max": 22.0, "humid_min": 35.0, "humid_max": 65.0},
    # Printemps (mar, avr, mai)
     3: {"temp_min": 8.0,  "temp_max": 26.0, "humid_min": 30.0, "humid_max": 65.0},
     4: {"temp_min": 8.0,  "temp_max": 26.0, "humid_min": 30.0, "humid_max": 65.0},
     5: {"temp_min": 10.0, "temp_max": 28.0, "humid_min": 30.0, "humid_max": 65.0},
    # Été (jun, jui, aoû) — risques : chaleur, sécheresse ou condensation
     6: {"temp_min": 12.0, "temp_max": 32.0, "humid_min": 25.0, "humid_max": 70.0},
     7: {"temp_min": 14.0, "temp_max": 35.0, "humid_min": 20.0, "humid_max": 75.0},
     8: {"temp_min": 14.0, "temp_max": 35.0, "humid_min": 20.0, "humid_max": 75.0},
    # Automne (sep, oct, nov)
     9: {"temp_min": 10.0, "temp_max": 30.0, "humid_min": 30.0, "humid_max": 68.0},
    10: {"temp_min": 8.0,  "temp_max": 27.0, "humid_min": 30.0, "humid_max": 65.0},
    11: {"temp_min": 5.0,  "temp_max": 24.0, "humid_min": 35.0, "humid_max": 65.0},
}

# Fenêtre (en heures) du filtre de lissage (moyenne mobile)
FENETRE_LISSAGE = 3


# ─────────────────────────────────────────────────────────────────────────────
#  1. TRAITEMENT DU SIGNAL — Pré-traitement des séries temporelles
# ─────────────────────────────────────────────────────────────────────────────

def interpoler_valeurs_manquantes(serie: pd.Series) -> pd.Series:
    """
    Comble les NaN par interpolation linéaire (méthode "time" si index datetime,
    sinon "linear"). Les NaN en tête/queue sont remplis par propagation (bfill/ffill).

    Référence :
        Moritz & Bartz-Beielstein (2017). imputeTS: Time Series Missing Value
        Imputation in R. The R Journal 9(1), 207–218.

    Paramètres
    ----------
    serie : pd.Series — signal brut pouvant contenir des NaN

    Retourne
    --------
    pd.Series lissée sans NaN
    """
    if serie.isna().all():
        # Cas dégénéré : toute la série est vide → retourner une série de zéros
        return pd.Series(0.0, index=serie.index)

    # Interpolation linéaire centrale
    serie_interp = serie.interpolate(method="linear", limit_direction="both")
    # Compléter les extrémités résiduelles
    serie_interp = serie_interp.ffill().bfill()
    return serie_interp


def lisser_signal(serie: pd.Series,
                  fenetre: int = FENETRE_LISSAGE) -> pd.Series:
    """
    Applique un filtre de moyenne mobile (rolling mean) pour atténuer le bruit
    électronique des capteurs IoT.

    Justification mathématique :
        x̂[t] = (1/w) × Σ_{k=0}^{w-1} x[t-k]
    où w = fenetre (taille de la fenêtre glissante).

    Note : min_periods=1 évite les NaN en début de série (comportement "causal").

    Paramètres
    ----------
    serie   : pd.Series — signal à lisser (après interpolation)
    fenetre : int       — nombre de points dans la fenêtre (défaut = 3 h)

    Retourne
    --------
    pd.Series — signal lissé ∈ même domaine que l'entrée
    """
    return serie.rolling(window=fenetre, min_periods=1).mean()


def pretraiter_serie_capteurs(df_capteurs: pd.DataFrame,
                               colonnes: list = None) -> pd.DataFrame:
    """
    Pipeline complet de traitement du signal pour un DataFrame multi-capteurs :
        1. Interpolation linéaire des NaN par capteur
        2. Filtre de moyenne mobile par capteur
        3. Calcul de la moyenne agrégée (consensus multi-capteurs)

    Paramètres
    ----------
    df_capteurs : pd.DataFrame
        Colonnes attendues : ['capteur1', 'capteur2', 'capteur3'] (ou sous-ensemble)
    colonnes : list | None
        Liste des colonnes capteurs à utiliser (auto-détectées si None)

    Retourne
    --------
    pd.DataFrame avec colonnes originales traitées + 'valeur_moyenne' ajoutée
    """
    df = df_capteurs.copy()

    if colonnes is None:
        # Auto-détecter les colonnes capteurs (colonnes numériques hors 'datetime', 'id_entrepot')
        colonnes = [c for c in df.columns
                    if c not in ("datetime", "id_entrepot") and pd.api.types.is_numeric_dtype(df[c])]

    for col in colonnes:
        # Étape 1 : interpoler les NaN
        df[col] = interpoler_valeurs_manquantes(df[col])
        # Étape 2 : lisser le bruit
        df[col] = lisser_signal(df[col])

    # Agrégation multi-capteurs : moyenne simple des capteurs disponibles
    df["valeur_moyenne"] = df[colonnes].mean(axis=1)

    return df


# ─────────────────────────────────────────────────────────────────────────────
#  2. SCORE ENVIRONNEMENTAL DE BASE
# ─────────────────────────────────────────────────────────────────────────────

def calculate_environmental_score(total_hours: int,
                                  temp_anomalies_count: int,
                                  humid_anomalies_count: int) -> float:
    """
    Calcule un score de performance environnementale sur 100.
    100 = Parfait (aucune anomalie)
      0 = Catastrophique (anomalies permanentes)

    Formule (pondération HACCP) :
        taux_temp   = (N_h - N_anom_t)  / N_h × 100
        taux_humid  = (N_h - N_anom_h)  / N_h × 100
        score_final = taux_temp × WEIGHT_TEMP + taux_humid × WEIGHT_HUMID

    Pondération : WEIGHT_TEMP = 70 %, WEIGHT_HUMID = 30 %
    (Source : Codex Alimentarius CAC/RCP 1-1969, Rev. 4-2003)
    """
    if total_hours == 0:
        return 0.0

    temp_compliance  = ((total_hours - temp_anomalies_count)  / total_hours) * 100
    humid_compliance = ((total_hours - humid_anomalies_count) / total_hours) * 100

    final_score = (temp_compliance * WEIGHT_TEMP) + (humid_compliance * WEIGHT_HUMID)
    return round(final_score, 1)


def get_score_label(score: float) -> tuple:
    """Retourne une appréciation qualitative + emoji du score environnemental."""
    if score >= 90: return "Excellent",           "🟢"
    if score >= 75: return "Bon",                 "🟡"
    if score >= 50: return "Moyen (Risque)",      "🟠"
    return "Critique (Action requise)",            "🔴"


# ─────────────────────────────────────────────────────────────────────────────
#  3. NORMALISATION MIN-MAX (élimination du biais km vs %)
# ─────────────────────────────────────────────────────────────────────────────

def normalize_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise les métriques sur [0, 1] pour éliminer le biais d'unité
    (km vs pourcentage vs points bruts).

    Règles par colonne :
        'distance'  → 1/d puis normalisation min-max (proximité = score élevé)
                       distance_norm = (1/d) / max(1/d)
        'score_iot' → normalisation min-max classique
                       score_iot_norm = (x - min) / (max - min)

    Justification de l'inverse (1/d) :
        Un entrepôt à 10 km doit scorer > un entrepôt à 500 km.
        L'inverse renverse le sens et la normalisation max-scale ramène à [0,1].
        (réf. Meng, 2020 — Distance-Based Multi-Criteria Decision Making)

    Paramètres
    ----------
    df : pd.DataFrame avec colonnes 'distance' et/ou 'score_iot'

    Retourne
    --------
    pd.DataFrame enrichi de 'distance_norm' et 'score_iot_norm'
    """
    df = df.copy()

    # ── Normalisation distance (inverse + min-max) ───────────────────────────
    if "distance" in df.columns:
        dist_safe = df["distance"].replace(0, np.nan).fillna(1e-6)
        inverse_dist = 1.0 / dist_safe          # proximité → valeur haute
        max_inv = inverse_dist.max()
        df["distance_norm"] = (inverse_dist / max_inv).round(4) if max_inv > 0 else 0.0
    else:
        df["distance_norm"] = 0.5   # valeur neutre si colonne absente

    # ── Normalisation score IoT (min-max classique) ──────────────────────────
    if "score_iot" in df.columns:
        s_min = df["score_iot"].min()
        s_max = df["score_iot"].max()
        if s_max > s_min:
            df["score_iot_norm"] = ((df["score_iot"] - s_min) / (s_max - s_min)).round(4)
        else:
            df["score_iot_norm"] = 1.0   # dégénéré : tous scores identiques
    else:
        df["score_iot_norm"] = 0.5

    return df


# ─────────────────────────────────────────────────────────────────────────────
#  4. FUSION SAW 60/40 — Score Global
# ─────────────────────────────────────────────────────────────────────────────

def calculer_score_global(score_log: Optional[float],
                           score_env: Optional[float]) -> float:
    """
    Fusionne les deux axes selon la règle SAW 60/40 :

        Score_Global = 0.60 × score_log + 0.40 × score_env

    Gestion des valeurs manquantes :
        None → remplacé par le score neutre 50.0
        Valeurs hors [0, 100] → clampées (sécurité)

    Référence SAW :
        MacCrimmon, K.R. (1968). Decision Making Among Multiple-Attribute
        Alternatives: A Survey and Consolidated Approach. Rand Corp.
    """
    s_log = float(score_log) if score_log is not None else SCORE_LOG_DEFAUT
    s_env = float(score_env) if score_env is not None else SCORE_ENV_DEFAUT

    # Sécurité : clamp dans [0, 100]
    s_log = max(0.0, min(100.0, s_log))
    s_env = max(0.0, min(100.0, s_env))

    score_global = POIDS_LOGISTIQUE * s_log + POIDS_ENVIRONNEMENT * s_env
    return round(score_global, 2)


# ─────────────────────────────────────────────────────────────────────────────
#  5. ANALYSE SAISONNIÈRE & CONFORMITÉ AUX NORMES
# ─────────────────────────────────────────────────────────────────────────────

def get_saison(mois: int) -> str:
    """Retourne le nom de la saison pour un mois donné (1-12)."""
    if mois in (12, 1, 2):  return "Hiver"
    if mois in (3, 4, 5):   return "Printemps"
    if mois in (6, 7, 8):   return "Été"
    return "Automne"


def analyser_conformite_mensuelle(df: pd.DataFrame,
                                   col_temp: str = "valeur_moyenne",
                                   col_datetime: str = "datetime") -> pd.DataFrame:
    """
    Segmente les données IoT par mois et calcule le taux de conformité
    de chaque mois par rapport aux normes industrielles HACCP saisonnières.

    Paramètres
    ----------
    df          : pd.DataFrame avec colonnes datetime et température moyenne
    col_temp    : str — nom de la colonne de température moyenne traitée
    col_datetime: str — nom de la colonne datetime

    Retourne
    --------
    pd.DataFrame mensuel avec colonnes :
        'mois', 'saison', 'temp_moy', 'temp_std', 'n_releves',
        'norm_temp_min', 'norm_temp_max',
        'taux_conformite_temp' (%), 'statut_mois'
    """
    df = df.copy()
    df[col_datetime] = pd.to_datetime(df[col_datetime])
    df["mois"] = df[col_datetime].dt.month

    rows = []
    for mois, groupe in df.groupby("mois"):
        norme = NORMES_SAISONNIERES.get(mois, NORMES_SAISONNIERES[6])
        temp_vals = groupe[col_temp].dropna()

        if temp_vals.empty:
            continue

        n = len(temp_vals)
        temp_moy = round(temp_vals.mean(), 2)
        temp_std = round(temp_vals.std(), 2)

        # Taux de conformité : fraction de relevés dans [temp_min, temp_max]
        conformes = ((temp_vals >= norme["temp_min"]) &
                     (temp_vals <= norme["temp_max"])).sum()
        taux = round(conformes / n * 100, 1)

        # Statut du mois
        if taux >= 90:
            statut = "✅ Conforme"
        elif taux >= 70:
            statut = "⚠️ Vigilance"
        else:
            statut = "🔴 Hors-norme"

        rows.append({
            "mois":                int(mois),
            "saison":              get_saison(int(mois)),
            "temp_moy":            temp_moy,
            "temp_std":            temp_std,
            "n_releves":           n,
            "norm_temp_min":       norme["temp_min"],
            "norm_temp_max":       norme["temp_max"],
            "taux_conformite_temp": taux,
            "statut_mois":         statut,
        })

    return pd.DataFrame(rows).sort_values("mois").reset_index(drop=True)


def analyser_conformite_mensuelle_humidite(df: pd.DataFrame,
                                            col_humid: str = "valeur_moyenne",
                                            col_datetime: str = "datetime") -> pd.DataFrame:
    """
    Segmentation mensuelle pour l'humidité (même logique que la température).
    Référence aux normes saisonnières NORMES_SAISONNIERES.
    """
    df = df.copy()
    df[col_datetime] = pd.to_datetime(df[col_datetime])
    df["mois"] = df[col_datetime].dt.month

    rows = []
    for mois, groupe in df.groupby("mois"):
        norme = NORMES_SAISONNIERES.get(mois, NORMES_SAISONNIERES[6])
        h_vals = groupe[col_humid].dropna()

        if h_vals.empty:
            continue

        n = len(h_vals)
        h_moy = round(h_vals.mean(), 2)
        h_std = round(h_vals.std(), 2)

        conformes = ((h_vals >= norme["humid_min"]) &
                     (h_vals <= norme["humid_max"])).sum()
        taux = round(conformes / n * 100, 1)

        if taux >= 90:   statut = "✅ Conforme"
        elif taux >= 70: statut = "⚠️ Vigilance"
        else:            statut = "🔴 Hors-norme"

        rows.append({
            "mois":                  int(mois),
            "saison":                get_saison(int(mois)),
            "humid_moy":             h_moy,
            "humid_std":             h_std,
            "n_releves":             n,
            "norm_humid_min":        norme["humid_min"],
            "norm_humid_max":        norme["humid_max"],
            "taux_conformite_humid": taux,
            "statut_mois":           statut,
        })

    return pd.DataFrame(rows).sort_values("mois").reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
#  6. MOTEUR DE RECOMMANDATION INTELLIGENT
# ─────────────────────────────────────────────────────────────────────────────

def generer_conseil(score_global: float,
                    score_log: Optional[float],
                    score_env: Optional[float],
                    mois_courant: Optional[int] = None) -> dict:
    """
    Génère une recommandation intelligente multi-axes avec conscience saisonnière.

    Logique de décision :
        1. Détermination du statut global (Optimal / Acceptable / Critique)
        2. Identification de l'axe faible (Logistique vs Environnement)
        3. Enrichissement saisonnier (alerte chaleur en été, gel en hiver)

    Paramètres
    ----------
    score_global  : float — score final SAW [0-100]
    score_log     : float | None — axe logistique
    score_env     : float | None — axe environnement
    mois_courant  : int | None — mois (1-12), auto-détecté si None

    Retourne
    --------
    dict :
        'statut'      : 'Optimal' | 'Acceptable' | 'Critique'
        'texte'       : Justification textuelle complète
        'action'      : Action corrective recommandée (avec contexte saisonnier)
        'couleur'     : Code hex (pour UI Streamlit)
        'emoji'       : Indicateur visuel
        'alerte_saisonniere' : str — remarque environnementale contextuelle
    """
    s_log = float(score_log) if score_log is not None else SCORE_LOG_DEFAUT
    s_env = float(score_env) if score_env is not None else SCORE_ENV_DEFAUT

    # ── Statut global ────────────────────────────────────────────────────────
    if score_global >= 75:
        statut = "Optimal";    couleur = "#27ae60"; emoji = "✅"
    elif score_global >= 50:
        statut = "Acceptable"; couleur = "#f39c12"; emoji = "⚠️"
    else:
        statut = "Critique";   couleur = "#e74c3c"; emoji = "🔴"

    # ── Analyse de l'axe faible ──────────────────────────────────────────────
    diff = s_log - s_env   # positif → Env est le maillon faible

    if abs(diff) <= 5:
        texte_axe = (
            f"Les deux axes sont équilibrés "
            f"(Logistique: {s_log:.1f}/100 | Environnement: {s_env:.1f}/100)."
        )
    elif diff > 5:
        texte_axe = (
            f"L'axe Environnement ({s_env:.1f}/100) pénalise la note finale "
            f"par rapport à l'axe Logistique ({s_log:.1f}/100). "
            f"Écart de {diff:.1f} points."
        )
    else:
        texte_axe = (
            f"L'axe Logistique ({s_log:.1f}/100) est le facteur limitant "
            f"par rapport à l'axe Environnement ({s_env:.1f}/100). "
            f"Écart de {abs(diff):.1f} points."
        )

    texte = (
        f"Score global de {score_global:.1f}/100 — Statut : {statut}. "
        f"{texte_axe}"
    )

    # ── Sélection de l'action corrective ─────────────────────────────────────
    if statut == "Optimal":
        action = "✅ Entrepôt opérationnel — Confirmer la réservation."
    elif statut == "Critique":
        if diff > 5:
            if s_env < 40:
                action = ("🔧 Action urgente : Prévoir une isolation thermique "
                          "et un système de climatisation automatique "
                          "(régulation T°/Humidité hors-normes HACCP).")
            else:
                action = ("🌡️ Améliorer la régulation environnementale : "
                          "calibrer les alertes capteurs et vérifier les systèmes CVC.")
        else:
            action = ("🚚 Revoir la chaîne logistique : l'entrepôt est trop éloigné "
                      "ou présente trop d'incidents opérationnels.")
    else:  # Acceptable
        if diff > 5:
            action = ("🌡️ Surveiller l'axe Environnemental : envisager une isolation "
                      "thermique ou une mise à niveau des capteurs IoT.")
        elif diff < -5:
            action = ("🚚 Optimiser la logistique : négocier des contrats de transport "
                      "ou rechercher un entrepôt plus proche du centre de gravité.")
        else:
            action = "📊 Maintenir la surveillance des deux axes — révision recommandée dans 30 jours."

    # ── Alerte saisonnière contextuelle ──────────────────────────────────────
    mois = mois_courant or datetime.now().month
    saison = get_saison(mois)
    norme = NORMES_SAISONNIERES.get(mois, NORMES_SAISONNIERES[6])

    if saison == "Été":
        alerte = (
            f"☀️ Alerte estivale (mois {mois}) : attention à la montée en chaleur. "
            f"T° max autorisée : {norme['temp_max']}°C. "
            f"Vérifier la ventilation et la climatisation de l'entrepôt."
        )
    elif saison == "Hiver":
        alerte = (
            f"❄️ Alerte hivernale (mois {mois}) : risque de gel des marchandises. "
            f"T° min autorisée : {norme['temp_min']}°C. "
            f"Contrôler le système de chauffage et l'isolation des quais."
        )
    elif saison == "Printemps":
        alerte = (
            f"🌿 Printemps (mois {mois}) : humidité montante possible. "
            f"H% max : {norme['humid_max']}%. "
            f"Surveiller la condensation dans les zones de stockage basses."
        )
    else:  # Automne
        alerte = (
            f"🍂 Automne (mois {mois}) : variations rapides T°/Humidité. "
            f"Plage cible : [{norme['temp_min']}–{norme['temp_max']}]°C. "
            f"Planifier une inspection préventive avant l'hiver."
        )

    return {
        "statut":              statut,
        "texte":               texte,
        "action":              action,
        "couleur":             couleur,
        "emoji":               emoji,
        "alerte_saisonniere":  alerte,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  7. POINT D'ENTRÉE PRINCIPAL — calculer_decision_finale()
# ─────────────────────────────────────────────────────────────────────────────

def calculer_decision_finale(score_log: Optional[float],
                              score_env: Optional[float],
                              df_entrepots: Optional[pd.DataFrame] = None,
                              mois_courant: Optional[int] = None) -> dict:
    """
    Point d'entrée du moteur de décision OptiStock Phase 4.

    Pipeline :
        1. Fusion SAW 60/40 → score_global
        2. Moteur de recommandation → conseil avec alerte saisonnière
        3. (Optionnel) Normalisation Min-Max du DataFrame d'entrepôts

    Paramètres
    ----------
    score_log     : Score logistique [0-100] (None → fallback 50.0)
    score_env     : Score environnemental [0-100] (None → fallback 50.0)
    df_entrepots  : DataFrame optionnel à normaliser
    mois_courant  : Mois pour l'analyse saisonnière (None → mois actuel)

    Retourne
    --------
    dict :
        'score_global'    : float
        'score_log'       : float (valeur effective)
        'score_env'       : float (valeur effective)
        'conseil'         : dict (recommandation complète)
        'df_normalise'    : pd.DataFrame | None
    """
    # Étape 1 : Fusion SAW
    score_global = calculer_score_global(score_log, score_env)

    # Valeurs effectives avec fallbacks
    s_log_eff = float(score_log) if score_log is not None else SCORE_LOG_DEFAUT
    s_env_eff = float(score_env) if score_env is not None else SCORE_ENV_DEFAUT

    # Étape 2 : Recommandation intelligente (avec conscience saisonnière)
    conseil = generer_conseil(score_global, s_log_eff, s_env_eff, mois_courant)

    # Étape 3 : Normalisation du DataFrame si fourni
    df_norme = None
    if df_entrepots is not None and not df_entrepots.empty:
        df_norme = normalize_scores(df_entrepots)

    return {
        "score_global": score_global,
        "score_log":    s_log_eff,
        "score_env":    s_env_eff,
        "conseil":      conseil,
        "df_normalise": df_norme,
    }
