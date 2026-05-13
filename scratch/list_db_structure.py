import sqlite3

def list_tables_and_columns():
    conn = sqlite3.connect('database/optistock.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table_name in tables:
        print(f"\nTable: {table_name[0]}")
        cursor.execute(f"PRAGMA table_info({table_name[0]});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    conn.close()

if __name__ == "__main__":
    list_tables_and_columns()
