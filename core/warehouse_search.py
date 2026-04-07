from pathlib import Path

import numpy as np
import pandas as pd


TYPE_PARAMS = {
    "STANDARD": {
        "coef_t": 5.0,
        "coef_h": 5.0,
        "incident_temp": 2.0,
        "incident_hum": 2.0,
        "temp_reject_above": None,
        "hum_reject_above": None,
    },
    "FROID": {
        "coef_t": 8.0,
        "coef_h": 5.0,
        "incident_temp": 3.0,
        "incident_hum": 2.0,
        "temp_reject_above": 10.0,
        "hum_reject_above": None,
    },
    "SEC": {
        "coef_t": 4.0,
        "coef_h": 7.0,
        "incident_temp": 2.0,
        "incident_hum": 3.0,
        "temp_reject_above": None,
        "hum_reject_above": 55.0,
    },
    "CLIMATISE": {
        "coef_t": 6.0,
        "coef_h": 6.0,
        "incident_temp": 2.5,
        "incident_hum": 2.5,
        "temp_reject_above": 24.0,
        "hum_reject_above": 70.0,
    },
}


RELATION_EXPLANATIONS = [
    {
        "nom": "Extraction robuste",
        "formule": "T_heure = mediane(capteur1_t, capteur2_t, capteur3_t) ; H_heure = mediane(capteur1_h, capteur2_h, capteur3_h)",
        "justification": "La mediane est plus robuste qu'une moyenne quand un des trois capteurs est bruite, decale ou defectueux.",
        "impact": "Le signal horaire reste stable meme si un capteur part ponctuellement en erreur.",
    },
    {
        "nom": "Disponibilite",
        "formule": "P_dispo = moyenne(NaN temperature, NaN humidite) en pourcentage",
        "justification": "Un entrepot ne peut pas etre considere fiable si ses mesures sont absentes ou inexploitables.",
        "impact": "Les entrepots avec trous de donnees perdent des points meme si les valeurs existantes semblent bonnes.",
    },
    {
        "nom": "Coherence spatiale",
        "formule": "ecart spatial = (|C1 - V_nette| + |C2 - V_nette| + |C3 - V_nette|) / 3 ; P_coh = moyenne(ecarts) x 15",
        "justification": "Trois capteurs installes dans un meme entrepot doivent raconter une histoire proche. Un ecart important signale un probleme de capteur ou d'homogeneite.",
        "impact": "Plus les capteurs divergent entre eux, plus la penalite augmente.",
    },
    {
        "nom": "Baseline glissante",
        "formule": "baseline_t = moyenne mobile 24h(T_heure) ; baseline_h = moyenne mobile 24h(H_heure)",
        "justification": "Une baseline glissante capte le comportement recent normal sans imposer une valeur fixe a tous les entrepots.",
        "impact": "La detection d'anomalies se base sur le regime habituel de l'entrepot, pas sur un seuil arbitraire unique.",
    },
    {
        "nom": "Micro et macro depassements",
        "formule": "Micro: ecart > 3 degres ou 5 pourcent ; Macro: ecart > 7 degres ou 12 pourcent",
        "justification": "On distingue les petites deviations temporaires des vraies ruptures de fonctionnement pour ne pas sanctionner de la meme facon un bruit court et une panne longue.",
        "impact": "Les macros alimentent la penalite d'incident, les micros servent d'indicateur de fragilite.",
    },
    {
        "nom": "Instabilite saine",
        "formule": "P_instab = ecart-type de la courbe saine apres remplacement des macros par la baseline",
        "justification": "On veut mesurer la variabilite normale du systeme, sans que les grosses pannes masquent la qualite du fonctionnement courant.",
        "impact": "Un entrepot peut etre penalise meme sans panne majeure si sa regulation oscille trop.",
    },
    {
        "nom": "Ponderation par type",
        "formule": "Score = 100 - [P_dispo + P_coh + (P_instab_t x coef_t) + (P_instab_h x coef_h) + P_inc ajuste]",
        "justification": "Tous les types de stockage n'ont pas la meme sensibilite. Le froid penalise plus la temperature, le sec penalise plus l'humidite.",
        "impact": "Le meme entrepot peut obtenir un score different selon le besoin metier recherche.",
    },
    {
        "nom": "Filtre d'eligibilite",
        "formule": "Rejet si temperature moyenne ou humidite moyenne depassent le plafond du type recherche",
        "justification": "Avant de classer, il faut exclure les entrepots incompatibles avec le besoin metier minimal.",
        "impact": "Un entrepot peut etre techniquement stable mais quand meme refuse pour incompatibilite fonctionnelle.",
    },
]


def _label_from_score(score: float) -> tuple[str, str]:
    if score >= 90:
        return "Excellent", "#27ae60"
    if score >= 75:
        return "Tres bon", "#2ecc71"
    if score >= 60:
        return "Acceptable", "#f39c12"
    if score >= 40:
        return "Mauvais", "#e67e22"
    return "Inutilisable", "#c0392b"


def _incident_penalty(mask: pd.Series, weight: float) -> tuple[float, int]:
    active = mask.fillna(False).astype(bool)
    groups = active.ne(active.shift(fill_value=False)).cumsum()
    penalty = 0.0
    count = 0

    for _, incident in active[active].groupby(groups[active]):
        duration = len(incident)
        penalty += duration * weight
        count += 1

    return penalty, count


def _load_sensor_file(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required_columns = {"datetime", "capteur1", "capteur2", "capteur3"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans {path.name}: {', '.join(sorted(missing))}")

    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)
    return df


def calculate_entrepot_score(
    entrepot_id: str,
    type_recherche: str,
    data_dir: str | Path,
) -> dict:
    data_path = Path(data_dir)
    temp_path = data_path / f"temperature_{entrepot_id}.csv"
    humid_path = data_path / f"humidite_{entrepot_id}.csv"

    if not temp_path.exists() or not humid_path.exists():
        raise FileNotFoundError(f"Fichiers capteurs introuvables pour {entrepot_id}")

    params = TYPE_PARAMS.get(type_recherche.upper(), TYPE_PARAMS["STANDARD"])

    df_temp = _load_sensor_file(temp_path)
    df_hum = _load_sensor_file(humid_path)

    merged = pd.merge(
        df_temp[["datetime", "capteur1", "capteur2", "capteur3"]],
        df_hum[["datetime", "capteur1", "capteur2", "capteur3"]],
        on="datetime",
        how="inner",
        suffixes=("_t", "_h"),
    )

    if merged.empty:
        raise ValueError(f"Aucune plage horaire commune entre temperature et humidite pour {entrepot_id}")

    merged["T_heure"] = merged[["capteur1_t", "capteur2_t", "capteur3_t"]].median(axis=1)
    merged["H_heure"] = merged[["capteur1_h", "capteur2_h", "capteur3_h"]].median(axis=1)

    total_hours = len(merged)
    p_dispo_t = merged["T_heure"].isna().sum() / total_hours * 100
    p_dispo_h = merged["H_heure"].isna().sum() / total_hours * 100
    p_dispo = round((p_dispo_t + p_dispo_h) / 2, 2)

    merged["ecart_spatial_t"] = (
        (merged["capteur1_t"] - merged["T_heure"]).abs()
        + (merged["capteur2_t"] - merged["T_heure"]).abs()
        + (merged["capteur3_t"] - merged["T_heure"]).abs()
    ) / 3
    merged["ecart_spatial_h"] = (
        (merged["capteur1_h"] - merged["H_heure"]).abs()
        + (merged["capteur2_h"] - merged["H_heure"]).abs()
        + (merged["capteur3_h"] - merged["H_heure"]).abs()
    ) / 3
    p_coh = round(((merged["ecart_spatial_t"].mean() + merged["ecart_spatial_h"].mean()) / 2) * 15, 2)

    merged["baseline_t"] = merged["T_heure"].rolling(window=24, min_periods=1).mean()
    merged["baseline_h"] = merged["H_heure"].rolling(window=24, min_periods=1).mean()

    merged["ecart_baseline_t"] = (merged["T_heure"] - merged["baseline_t"]).abs()
    merged["ecart_baseline_h"] = (merged["H_heure"] - merged["baseline_h"]).abs()

    merged["is_macro_t"] = merged["ecart_baseline_t"] > 7.0
    merged["is_macro_h"] = merged["ecart_baseline_h"] > 12.0
    merged["is_micro_t"] = (merged["ecart_baseline_t"] > 3.0) & (~merged["is_macro_t"])
    merged["is_micro_h"] = (merged["ecart_baseline_h"] > 5.0) & (~merged["is_macro_h"])

    p_inc_t, nb_incidents_t = _incident_penalty(merged["is_macro_t"], params["incident_temp"])
    p_inc_h, nb_incidents_h = _incident_penalty(merged["is_macro_h"], params["incident_hum"])

    t_mean = float(merged["T_heure"].mean())
    h_mean = float(merged["H_heure"].mean())

    is_eligible = True
    reject_reason = None
    if params["temp_reject_above"] is not None and t_mean > params["temp_reject_above"]:
        is_eligible = False
        reject_reason = f"Temperature moyenne trop elevee pour {type_recherche}"
    if params["hum_reject_above"] is not None and h_mean > params["hum_reject_above"]:
        is_eligible = False
        reject_reason = f"Humidite moyenne trop elevee pour {type_recherche}"

    t_sain = merged["T_heure"].where(~merged["is_macro_t"], merged["baseline_t"]).dropna()
    h_sain = merged["H_heure"].where(~merged["is_macro_h"], merged["baseline_h"]).dropna()
    p_instab_t = float(t_sain.std(ddof=0)) if not t_sain.empty else 0.0
    p_instab_h = float(h_sain.std(ddof=0)) if not h_sain.empty else 0.0

    incident_adjusted = (p_inc_t + p_inc_h) * 0.05
    raw_score = 100 - (
        p_dispo
        + p_coh
        + (p_instab_t * params["coef_t"])
        + (p_instab_h * params["coef_h"])
        + incident_adjusted
    )
    score = round(float(np.clip(raw_score, 0, 100)), 2)

    if not is_eligible:
        score = 0.0

    label, color = _label_from_score(score)

    return {
        "id_entrepot": entrepot_id,
        "score": score,
        "label": "Rejete" if not is_eligible else label,
        "couleur": "#7f8c8d" if not is_eligible else color,
        "temp_moyenne": round(t_mean, 2),
        "hum_moyenne": round(h_mean, 2),
        "penalite_dispo": round(p_dispo, 2),
        "penalite_coherence": round(p_coh, 2),
        "penalite_instabilite_temp": round(p_instab_t * params["coef_t"], 2),
        "penalite_instabilite_hum": round(p_instab_h * params["coef_h"], 2),
        "penalite_incidents": round(incident_adjusted, 2),
        "nb_incidents": int(nb_incidents_t + nb_incidents_h),
        "nb_micro_temp": int(merged["is_micro_t"].sum()),
        "nb_micro_hum": int(merged["is_micro_h"].sum()),
        "eligible": is_eligible,
        "motif_rejet": reject_reason,
        "type_cherche": type_recherche,
        "heures_total": int(total_hours),
        "nan_temp": int(merged["T_heure"].isna().sum()),
        "nan_hum": int(merged["H_heure"].isna().sum()),
        "p_inc_temp_brut": round(p_inc_t, 2),
        "p_inc_hum_brut": round(p_inc_h, 2),
        "coef_temp": params["coef_t"],
        "coef_hum": params["coef_h"],
        "raw_score": round(raw_score, 2),
        "relations": RELATION_EXPLANATIONS,
    }


def search_entrepots(type_recherche: str, data_dir: str | Path) -> list[dict]:
    data_path = Path(data_dir)
    entrepot_ids = sorted(
        path.stem.replace("temperature_", "")
        for path in data_path.glob("temperature_ENT*.csv")
    )

    results = []
    for entrepot_id in entrepot_ids:
        try:
            results.append(calculate_entrepot_score(entrepot_id, type_recherche, data_path))
        except Exception:
            continue

    return sorted(results, key=lambda item: item["score"], reverse=True)
