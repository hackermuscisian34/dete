import sqlite3
import os
import re
from pathlib import Path
from config.settings import settings

def migrate():
    """
    Run database migrations to ensure schema matches SQLAlchemy models.
    """
    # Extract path from URL: sqlite+aiosqlite:////path/to/db or sqlite+aiosqlite:///C:/path
    db_url = settings.final_database_url
    print(f"DEBUG: Migration utility using URL: {db_url}")
    
    # regex to find path after protocol://
    match = re.search(r'://+(.*)', db_url)
    if match:
        db_path = match.group(1)
    else:
        db_path = db_url

    # Convert to Path object for easier handling
    path_obj = Path(db_path)
    
    # If it's not absolute, make it relative to project base
    if not path_obj.is_absolute() and not (os.name == 'nt' and len(db_path) > 1 and db_path[1] == ':'):
        db_path = str(settings.base_dir / db_path)
    
    # Final check for Unix style absolute paths if we are on Linux
    if os.name != 'nt' and not db_path.startswith('/'):
        # Force leading slash if it was stripped but we are on Linux
        db_path = '/' + db_path

    if not os.path.exists(db_path):
        # Try one last check relative to CWD
        if os.path.exists("data/defender.db"):
             db_path = "data/defender.db"
        elif os.path.exists("../data/defender.db"):
             db_path = "../data/defender.db"
        else:
            print(f"DEBUG: Database file not found at {db_path}. Migration skipped.")
            return

    print(f"DEBUG: Connecting to database for migration: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if total_files exists
        cursor.execute("PRAGMA table_info(scans)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "total_files" not in columns:
            print("DEBUG: Adding total_files column to scans table...")
            cursor.execute("ALTER TABLE scans ADD COLUMN total_files INTEGER DEFAULT 0")
            print("DEBUG: Successfully added total_files column.")
        else:
            print("DEBUG: total_files column already exists.")
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"ERROR: Migration failure: {e}")

if __name__ == "__main__":
    migrate()
