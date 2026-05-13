import sqlite3
import pandas as pd

def check_admins():
    try:
        conn = sqlite3.connect('database/optistock.db')
        query = "SELECT user_id, role, first_name, last_name, email FROM users WHERE role = 'admin';"
        df = pd.read_sql_query(query, conn)
        conn.close()
        if df.empty:
            print("Aucun administrateur trouvé.")
        else:
            print("Administrateurs trouvés :")
            print(df)
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    check_admins()
