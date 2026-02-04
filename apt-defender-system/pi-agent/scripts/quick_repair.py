import sqlite3
import os
from pathlib import Path

def repair():
<<<<<<< HEAD
    # Detect base directory (project root where 'data' folder lives)
    base_dir = Path(__file__).parent.parent.parent
=======
    # Detect base directory (pi-agent folder)
    base_dir = Path(__file__).parent.parent
>>>>>>> 0ba451690ecf6a7601979195acacecc80f940391
    db_path = base_dir / "data" / "defender.db"
    
    if not db_path.exists():
        print(f"❌ Error: Database not found at {db_path}")
        return

    print(f"🔍 Connecting to database: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # 1. Get the primary user
        cursor.execute("SELECT id, email FROM users ORDER BY id LIMIT 1")
        user = cursor.fetchone()
        
        if not user:
            print("❌ Error: No users found. Please log in to the mobile app first.")
            return
        
        user_id, email = user
        print(f"👤 Primary user found: {email} (ID: {user_id})")

        # 2. Get all devices
        cursor.execute("SELECT id, hostname FROM devices")
        devices = cursor.fetchall()
        print(f"🖥️ Found {len(devices)} devices.")

        repaired = 0
        for device_id, hostname in devices:
            # 3. Check if link exists
            cursor.execute("SELECT 1 FROM device_users WHERE device_id = ? AND user_id = ?", (device_id, user_id))
            if not cursor.fetchone():
                print(f"➕ Linking {hostname} (ID: {device_id}) -> {email}")
                cursor.execute(
                    "INSERT INTO device_users (device_id, user_id, access_level) VALUES (?, ?, 'owner')",
                    (device_id, user_id)
                )
                repaired += 1
            else:
                print(f"✅ {hostname} already linked.")

        conn.commit()
        print(f"✨ Success! Repaired {repaired} device associations.")
        print("📱 Refresh your mobile app now!")

    except Exception as e:
        print(f"❌ SQL Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    repair()
