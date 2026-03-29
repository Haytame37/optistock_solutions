from utils.constants import WEIGHT_TEMP, WEIGHT_HUMID

def calculate_environmental_score(total_hours, temp_anomalies_count, humid_anomalies_count):
    """
    Calcule un score de performance sur 100.
    100 = Parfait (aucune anomalie)
    0   = Catastrophique (anomalies permanentes)
    """
    # 1. Calcul du taux de conformité (en %)
    temp_compliance = ((total_hours - temp_anomalies_count) / total_hours) * 100
    humid_compliance = ((total_hours - humid_anomalies_count) / total_hours) * 100
    
    # 2. Application des coefficients (Poids)
    # Score = (Taux_T * Poids_T) + (Taux_H * Poids_H)
    final_score = (temp_compliance * WEIGHT_TEMP) + (humid_compliance * WEIGHT_HUMID)
    
    return round(final_score, 1)

def get_score_label(score):
    """Retourne une appréciation qualitative du score."""
    if score >= 90: return "Excellent", "🟢"
    if score >= 75: return "Bon", "🟡"
    if score >= 50: return "Moyen (Risque)", "🟠"
    return "Critique (Action requise)", "🔴"

