import pandas as pd
import numpy as np

# Paramètres du dataset
output_file = "C:/Users/rafik/optistock_solutions/historique_iot_2025.csv"

start_date = "2025-01-01"
end_date = "2025-12-31 23:59:59"
# Génération horaire sur toute l'année (8760 heures)
dates = pd.date_range(start=start_date, end=end_date, freq="h")
num_hours = len(dates)

# Configuration des 4 entrepôts présents dans vos tests
entrepots = [
    {"nom": "Hub Casablanca", "type": "Froid", "temp_base": 4.0, "temp_var_saison": 2.0, "temp_noise": 0.5, "hum_base": 85.0, "hum_noise": 3.0},
    {"nom": "Zone Tanger Med", "type": "Froid", "temp_base": 3.5, "temp_var_saison": 1.5, "temp_noise": 0.4, "hum_base": 82.0, "hum_noise": 2.5},
    {"nom": "Plateforme Marrakech", "type": "Froid", "temp_base": 5.0, "temp_var_saison": 3.0, "temp_noise": 0.8, "hum_base": 78.0, "hum_noise": 4.0},
    {"nom": "Entrepôt Béni Mellal", "type": "Sec", "temp_base": 20.0, "temp_var_saison": 8.0, "temp_noise": 1.5, "hum_base": 50.0, "hum_noise": 8.0},
]

all_data = []

# Pour que les résultats soient reproductibles
np.random.seed(42)

for ent in entrepots:
    # 1. Effet saisonnier : la température monte en été (vers les jours 150-240) et baisse en hiver.
    # On utilise un cosinus négatif décalé pour représenter l'année.
    jours_annee = np.arange(num_hours) / 24
    saison_effect = -np.cos(2 * np.pi * (jours_annee - 20) / 365.25) * ent["temp_var_saison"]
    
    # 2. Température de base + variabilité saisonnière + bruit blanc (fluctuations quotidiennes)
    temp = ent["temp_base"] + saison_effect + np.random.normal(0, ent["temp_noise"], num_hours)
    
    # 3. Ajout d'anomalies aléatoires (simulant de rares pannes de climatisation qui provoquent des pics de chaleur)
    anomalies = np.random.choice([0, 5], size=num_hours, p=[0.998, 0.002])
    temp += anomalies
    
    # 4. Génération de l'humidité relative avec un bruit blanc naturel
    hum = ent["hum_base"] + np.random.normal(0, ent["hum_noise"], num_hours)
    hum = np.clip(hum, 0, 100) # L'humidité ne peut pas dépasser 100% ou être inférieure à 0%
    
    # 5. Création du DataFrame pour cet entrepôt
    df = pd.DataFrame({
        "nom_entrepot": ent["nom"],
        "date": dates,
        "temperature": np.round(temp, 2), # Arrondi à 2 décimales
        "humidite": np.round(hum, 2)
    })
    
    all_data.append(df)

# Concaténation de tous les entrepôts
df_final = pd.concat(all_data, ignore_index=True)

# Sauvegarde en CSV
df_final.to_csv(output_file, index=False)
print(f"✅ {len(df_final)} relevés générés avec succès dans '{output_file}'.")
