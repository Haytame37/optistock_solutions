import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.constants import DAYS_IN_YEAR, HOURS_PER_DAY, DATA_PATH

def generate_iot_dataset():
    print("--- Démarrage de la simulation annuelle OptiStock ---")
    
    # 1. Création de la plage de temps (8760 points pour 1 an)
    start_date = datetime(2025, 1, 1)
    timestamps = [start_date + timedelta(hours=i) for i in range(DAYS_IN_YEAR * HOURS_PER_DAY)]
    
    # 2. Création de la courbe saisonnière (Cycle de 365 jours)
    # On utilise un sinus décalé pour que le minimum soit en hiver et le max en été
    time_index = np.arange(len(timestamps))
    annual_cycle = np.sin(2 * np.pi * time_index / (DAYS_IN_YEAR * HOURS_PER_DAY) - np.pi/2)
    
    # --- Température (°C) ---
    # Moyenne 20°C, oscille entre 10°C (hiver) et 30°C (été) + bruit aléatoire
    temp_base = 20 + 10 * annual_cycle
    temp_noise = np.random.normal(0, 1.5, len(timestamps))
    temperature = np.round(temp_base + temp_noise, 2)
    
    # --- Humidité (%) ---
    # Souvent plus haute quand il fait froid, plus basse quand il fait chaud
    humid_base = 50 - 15 * annual_cycle
    humid_noise = np.random.normal(0, 4, len(timestamps))
    humidity = np.round(np.clip(humid_base + humid_noise, 15, 90), 2)
    
    # 3. Création du DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'capteur_id': 'SN-TDI-2026-001', # Un ID pro pour ton club Industrie 4.0
        'temperature': temperature,
        'humidite': humidity
    })
    
    # 4. Sauvegarde dans le bon dossier
    df.to_csv(DATA_PATH, index=False)
    print(f"✅ Dataset généré avec succès : {DATA_PATH}")
    print(f"📊 Nombre de lignes : {len(df)}")

if __name__ == "__main__":
    generate_iot_dataset()