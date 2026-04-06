import pandas as pd
import os

# Configuration des chemins
INPUT_DIR = "data/samples/"
OUTPUT_DIR = "data/cleaned/"

# Création du dossier de sortie s'il n'existe pas
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_client_data(df):
    """Nettoyage spécifique aux fichiers clients_batch_XX.csv"""
    # 1. Supprimer les doublons sur l'ID client
    df = df.drop_duplicates(subset=['client_id'])
    # 2. Vérifier les coordonnées (ex: lat entre 20 et 36 pour le Maroc)
    df = df[(df['lat'].between(20, 37)) & (df['lon'].between(-14, 0))]
    # 3. Uniformiser les types (ex: tout en minuscule)
    # On ajoute .str devant .strip()
    df['type_requis'] = df['type_requis'].str.lower().str.strip()
    return df

def clean_iot_data(df):
    """Nettoyage pour les fichiers température/humidité"""
    # 1. Convertir la colonne temps en datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    # 2. Gérer les valeurs manquantes (interpolation ou suppression)
    df = df.interpolate(method='linear')
    # 3. Supprimer les aberrations (ex: température > 60°C ou < -20°C)
    if 'valeur' in df.columns:
        df = df[df['valeur'].between(-20, 60)]
    return df

# Boucle principale de traitement
for filename in os.listdir(INPUT_DIR):
    if filename.endswith(".csv"):
        print(f"Traitement de {filename}...")
        df = pd.read_csv(os.path.join(INPUT_DIR, filename))
        
        if "clients" in filename:
            df_cleaned = clean_client_data(df)
        elif "temperature" in filename or "humidite" in filename:
            df_cleaned = clean_iot_data(df)
        else:
            df_cleaned = df # Traitement par défaut
            
        df_cleaned.to_csv(os.path.join(OUTPUT_DIR, filename), index=False)

print("✅ Nettoyage terminé. Les fichiers sont dans data/cleaned/")