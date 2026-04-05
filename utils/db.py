import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "optistock.db")

def get_db_connection():
    """Crée et retourne une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DB_PATH)
    # Permet d'accéder aux colonnes via leur nom au lieu d'un index
    conn.row_factory = sqlite3.Row 
    return conn

def execute_query(query, params=()):
    """Exécute une requête (INSERT, UPDATE, DELETE) et commit."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def load_sql_to_dataframe(query, params=()):
    """Exécute une requête SELECT et la charge directement dans un DataFrame Pandas."""
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
