import pandas as pd
import sqlite3
import os
import glob

DB_PATH = os.path.join(os.path.dirname(__file__), "optistock.db")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "samples")

def seed_database():
    """Charge les données CSV générées (fichiers chunkés) dans la base SQLite."""
    print("🌱 Démarrage de l'importation vers SQLite (Batch)...")
    
    if not os.path.exists(DB_PATH):
        print("❌ La base optistock.db n'existe pas. Exécutez init_db.py d'abord.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Importation du Catalogue Entrepôts (entrepots.csv)
    entrepots_csv = os.path.join(DATA_DIR, "entrepots.csv")
    if os.path.exists(entrepots_csv):
        df_entrepots = pd.read_csv(entrepots_csv)
        print(f"📦 Importation de {len(df_entrepots)} entrepôts dans la BDD...")
        # Comme type_stockage, nom et volume ne sont pas dans le CSV du build, 
        # sqlite va utiliser les default values si on laisse les colonnes manquantes
        df_entrepots.to_sql("entrepots", conn, if_exists="append", index=False)
    else:
        print("⚠️ Fichier entrepots.csv introuvable.")

    # 2. Importation des chunks de Température (temperature_ENT*.csv)
    temp_files = glob.glob(os.path.join(DATA_DIR, "temperature_ENT*.csv"))
    if temp_files:
        print(f"🌡️ Importation de {len(temp_files)} fichiers de température...")
        for f in temp_files:
            df_temp = pd.read_csv(f)
            df_temp.to_sql("temperature", conn, if_exists="append", index=False)
    else:
        print("⚠️ Aucun fichier temperature_ENT*.csv trouvé.")

    # 3. Importation des chunks d'Humidité (humidite_ENT*.csv)
    hum_files = glob.glob(os.path.join(DATA_DIR, "humidite_ENT*.csv"))
    if hum_files:
        print(f"💧 Importation de {len(hum_files)} fichiers d'humidité...")
        for f in hum_files:
            df_hum = pd.read_csv(f)
            df_hum.to_sql("humidite", conn, if_exists="append", index=False)
    else:
        print("⚠️ Aucun fichier humidite_ENT*.csv trouvé.")
        
    conn.commit()
    conn.close()
    print("✅ Base de données SQLite peuplée avec succès !")

if __name__ == "__main__":
    seed_database()
