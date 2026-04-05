import pandas as pd
from utils.constants import TEMP_MIN, TEMP_MAX, HUMID_MIN, HUMID_MAX

def load_iot_data(filepath):
    """Charge un dataset et s'assure que les dates sont au bon format."""
    df = pd.read_csv(filepath)
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df

def get_basic_stats(df_temp, df_humid):
    """Calcule les statistiques en faisant la moyenne des 3 capteurs."""
    # Calcul de la moyenne des capteurs par ligne
    df_t_mean = df_temp[['capteur1', 'capteur2', 'capteur3']].mean(axis=1)
    df_h_mean = df_humid[['capteur1', 'capteur2', 'capteur3']].mean(axis=1)
    
    return {
        "temp_mean": round(df_t_mean.mean(), 2),
        "temp_min": round(df_t_mean.min(), 2),
        "temp_max": round(df_t_mean.max(), 2),
        "temp_std": round(df_t_mean.std(), 2),
        "humid_mean": round(df_h_mean.mean(), 2),
        "humid_min": round(df_h_mean.min(), 2),
        "humid_max": round(df_h_mean.max(), 2),
        "humid_std": round(df_h_mean.std(), 2)
    }

def detect_anomalies(df_temp, df_humid):
    """
    Isole les lignes où les seuils environnementaux sont franchis.
    Utilise la moyenne des 3 capteurs pour valider le dépassement.
    """
    t_avg = df_temp[['capteur1', 'capteur2', 'capteur3']].mean(axis=1)
    mask_temp = (t_avg < TEMP_MIN) | (t_avg > TEMP_MAX)
    anomalies_temp = df_temp[mask_temp]
    
    h_avg = df_humid[['capteur1', 'capteur2', 'capteur3']].mean(axis=1)
    mask_humid = (h_avg < HUMID_MIN) | (h_avg > HUMID_MAX)
    anomalies_humid = df_humid[mask_humid]
    
    return anomalies_temp, anomalies_humid

# --- BLOC DE TEST (Le point d'entrée) ---
if __name__ == "__main__":
    from core.scoring import calculate_environmental_score, get_score_label
    from utils.constants import TEMP_DATA_PATH, HUMID_DATA_PATH
    
    # 1. Pipeline
    df_t = load_iot_data(TEMP_DATA_PATH)
    df_h = load_iot_data(HUMID_DATA_PATH)
    stats = get_basic_stats(df_t, df_h)
    bad_temp, bad_humid = detect_anomalies(df_t, df_h)
    
    # 2. Score
    # On suppose que le nombre total d'heures est le max des deux
    total_len = max(len(df_t), len(df_h))
    score = calculate_environmental_score(total_len, len(bad_temp), len(bad_humid))
    label, emoji = get_score_label(score)
    
    # 3. Affichage
    print("\n" + "="*30)
    print(f"📊 RAPPORT OPTISTOCK (Multi-Capteurs)")
    print("="*30)
    print(f"🌡️ Température Moyenne : {stats['temp_mean']}°C")
    print(f"💧 Humidité Moyenne    : {stats['humid_mean']}%")
    print("-" * 30)
    print(f"🚨 Alertes Température : {len(bad_temp)} heures")
    print(f"🚨 Alertes Humidité    : {len(bad_humid)} heures")
    print("-" * 30)
    print(f"⭐ SCORE FINAL : {score}/100 {emoji}")
    print(f"📢 Verdict     : {label}")
    print("="*30 + "\n")