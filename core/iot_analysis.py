import pandas as pd
from utils.constants import TEMP_MIN, TEMP_MAX, HUMID_MIN, HUMID_MAX

def load_iot_data(filepath):
    """Charge le dataset et s'assure que les dates sont au bon format."""
    df = pd.read_csv(filepath)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def get_basic_stats(df):
    """Calcule les statistiques descriptives globales pour l'entrepôt."""
    return {
        "temp_mean": round(df['temperature'].mean(), 2),
        "temp_min": df['temperature'].min(),
        "temp_max": df['temperature'].max(),
        "temp_std": round(df['temperature'].std(), 2), # Ajout de l'écart-type
        "humid_mean": round(df['humidite'].mean(), 2),
        "humid_min": df['humidite'].min(),
        "humid_max": df['humidite'].max(),
        "humid_std": round(df['humidite'].std(), 2)    # Ajout de l'écart-type
    }

def detect_anomalies(df):
    """
    Isole les lignes où les seuils environnementaux sont franchis.
    Retourne deux DataFrames : un pour la température, un pour l'humidité.
    """
    # Masques booléens pour les dépassements de température
    mask_temp = (df['temperature'] < TEMP_MIN) | (df['temperature'] > TEMP_MAX)
    anomalies_temp = df[mask_temp]
    
    # Masques booléens pour les dépassements d'humidité
    mask_humid = (df['humidite'] < HUMID_MIN) | (df['humidite'] > HUMID_MAX)
    anomalies_humid = df[mask_humid]
    
    return anomalies_temp, anomalies_humid

#TEST TEST tEST TEST #
# --- BLOC DE TEST (Le point d'entrée) ---
if __name__ == "__main__":
    from core.scoring import calculate_environmental_score, get_score_label
    from utils.constants import DATA_PATH
    
    # 1. Pipeline
    df_test = load_iot_data(DATA_PATH)
    stats = get_basic_stats(df_test)
    bad_temp, bad_humid = detect_anomalies(df_test)
    
    # 2. Score
    score = calculate_environmental_score(len(df_test), len(bad_temp), len(bad_humid))
    label, emoji = get_score_label(score)
    
    # 3. Affichage
    print("\n" + "="*30)
    print(f"📊 RAPPORT OPTISTOCK - 2026")
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