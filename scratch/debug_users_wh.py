import sqlite3

def debug_data():
    conn = sqlite3.connect('database/optistock.db')
    cursor = conn.cursor()
    
    print("--- USERS ---")
    cursor.execute("SELECT user_id, role, email FROM users")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- WAREHOUSES ---")
    cursor.execute("SELECT warehouse_id, owner_id, name FROM warehouses")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    debug_data()
