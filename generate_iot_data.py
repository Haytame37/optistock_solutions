import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.constants import DAYS_IN_YEAR, HOURS_PER_DAY

def generate_iot_dataset():
    print("--- Démarrage de la simulation annuelle OptiStock (Multi-Capteurs) ---")
    
    # 1. Création de la plage de temps (8760 points pour 1 an)
    start_date = datetime(2025, 1, 1)
    timestamps = [start_date + timedelta(hours=i) for i in range(DAYS_IN_YEAR * HOURS_PER_DAY)]
    
    # 2. Création de la courbe saisonnière (Cycle de 365 jours)
    time_index = np.arange(len(timestamps))
    annual_cycle = np.sin(2 * np.pi * time_index / (DAYS_IN_YEAR * HOURS_PER_DAY) - np.pi/2)
    
    # --- Température (°C) ---
    temp_base = 20 + 10 * annual_cycle
    t_cap1 = np.round(temp_base + np.random.normal(0, 1.5, len(timestamps)), 2)
    t_cap2 = np.round(temp_base + np.random.normal(0, 1.8, len(timestamps)), 2)
    t_cap3 = np.round(temp_base + np.random.normal(0, 1.2, len(timestamps)), 2)
    
    # --- Humidité (%) ---
    humid_base = 50 - 15 * annual_cycle
    h_cap1 = np.round(np.clip(humid_base + np.random.normal(0, 4.0, len(timestamps)), 15, 90), 2)
    h_cap2 = np.round(np.clip(humid_base + np.random.normal(0, 5.0, len(timestamps)), 15, 90), 2)
    h_cap3 = np.round(np.clip(humid_base + np.random.normal(0, 3.5, len(timestamps)), 15, 90), 2)
    
    # 3. Création des DataFrames
    id_entrepot = 'ENT_DEMO'
    id_proprietaire = 'OWN_DEMO'
    
    id_temp_array = [f"TMP-{id_entrepot}-{i+1:05d}" for i in range(len(timestamps))]
    id_hum_array = [f"HUM-{id_entrepot}-{i+1:05d}" for i in range(len(timestamps))]
    
    df_temp = pd.DataFrame({
        'id': id_temp_array,
        'id_entrepot': [id_entrepot] * len(timestamps),
        'datetime': timestamps,
        'capteur1': t_cap1,
        'capteur2': t_cap2,
        'capteur3': t_cap3
    })
    
    df_humid = pd.DataFrame({
        'id': id_hum_array,
        'id_entrepot': [id_entrepot] * len(timestamps),
        'id_proprietaire': [id_proprietaire] * len(timestamps),
        'datetime': timestamps,
        'capteur1': h_cap1,
        'capteur2': h_cap2,
        'capteur3': h_cap3
    })
    
    from utils.constants import TEMP_DATA_PATH, HUMID_DATA_PATH
    
    # 4. Sauvegarde
    df_temp.to_csv(TEMP_DATA_PATH, index=False)
    df_humid.to_csv(HUMID_DATA_PATH, index=False)
    
    print(f"✅ Datasets générés avec succès : {TEMP_DATA_PATH} et {HUMID_DATA_PATH}")
    print(f"📊 Nombre de lignes par fichier : {len(df_temp)}")

if __name__ == "__main__":
    generate_iot_dataset()