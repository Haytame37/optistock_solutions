import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "optistock.db")

def create_database():
    """Crée ou réinitialise la base de données avec le nouveau schéma."""
    
    # Supprimer la base existante pour repartir de zéro (Optionnel, mais utile en dev)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🔄 Ancienne base de données supprimée.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Pour s'assurer que les contraintes de clés étrangères sont respectées
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Table Catalogue Entrepot (Strictement basé sur vos colonnes + les nôtres avec des defauts)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entrepots (
            id_entrepot TEXT PRIMARY KEY,
            id_proprietaire TEXT NOT NULL,
            nom TEXT DEFAULT 'Entrepôt Sans Nom',
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            type_stockage TEXT DEFAULT 'mixte',
            volume INTEGER DEFAULT 10000
        )
    ''')

    # Table Température (Aura l'identifiant id_proprietaire pour symétrie si voulu, mais vous avez spécifié sans donc on s'aligne : id, id_entrepot, datetime, capteur 1,2,3)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temperature (
            id TEXT PRIMARY KEY,
            id_entrepot TEXT NOT NULL,
            datetime DATETIME NOT NULL,
            capteur1 REAL,
            capteur2 REAL,
            capteur3 REAL,
            FOREIGN KEY (id_entrepot) REFERENCES entrepots(id_entrepot) ON DELETE CASCADE
        )
    ''')

    # Table Humidité (Exemple avec id_proprietaire : id, id_entrepot, id_proprietaire, datetime, capteur1, capteur2, capteur3)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS humidite (
            id TEXT PRIMARY KEY,
            id_entrepot TEXT NOT NULL,
            id_proprietaire TEXT,
            datetime DATETIME NOT NULL,
            capteur1 REAL,
            capteur2 REAL,
            capteur3 REAL,
            FOREIGN KEY (id_entrepot) REFERENCES entrepots(id_entrepot) ON DELETE CASCADE
        )
    ''')

    # Créer des index pour accélérer les requêtes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_temp_entrepot ON temperature(id_entrepot);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hum_entrepot ON humidite(id_entrepot);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_temp_date ON temperature(datetime);")

    conn.commit()
    conn.close()
    
    print(f"✅ Base de données SQLite créée avec succès : {DB_PATH}")

if __name__ == "__main__":
    create_database()
