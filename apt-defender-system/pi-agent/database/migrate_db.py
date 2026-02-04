import sqlite3
import os
import sys

def migrate():
    db_path = "data/defender.db"
    if not os.path.exists(db_path):
        # If it's on the Pi and current dir is pi-agent
        db_path = "../data/defender.db"
        if not os.path.exists(db_path):
             print("Database not found. Skipping migration.")
             return

    print(f"Migrating database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if total_files exists
        cursor.execute("PRAGMA table_info(scans)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "total_files" not in columns:
            print("Adding total_files column to scans table...")
            cursor.execute("ALTER TABLE scans ADD COLUMN total_files INTEGER DEFAULT 0")
            print("Successfully added total_files column.")
        else:
            print("total_files column already exists.")
            
        conn.commit()
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
