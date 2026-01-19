import asyncio
import os
import sys
from pathlib import Path

# Add the pi-agent directory to sys.path to import modules
pi_agent_dir = Path(__file__).parent.parent
sys.path.append(str(pi_agent_dir))

from database.db import get_db, Device, User, DeviceUser
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

async def repair_associations():
    print("🔍 Starting Device-User Association Repair...")
    
    async for db in get_db():
        # 1. Get the primary user (usually the first one registered)
        result = await db.execute(select(User).order_by(User.id).limit(1))
        primary_user = result.scalar_one_or_none()
        
        if not primary_user:
            print("❌ Error: No users found in the database. Please register a user on the mobile app first.")
            return

        print(f"👤 Primary User found: {primary_user.email} (ID: {primary_user.id})")

        # 2. Get all devices
        result = await db.execute(select(Device))
        devices = result.scalars().all()
        print(f"🖥️ Found {len(devices)} total devices.")

        repaired_count = 0
        for device in devices:
            # Check if association already exists
            result = await db.execute(
                select(DeviceUser).where(
                    DeviceUser.device_id == device.id, 
                    DeviceUser.user_id == primary_user.id
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                print(f"➕ Linking orphaned device: {device.hostname} (ID: {device.id}) -> User ID: {primary_user.id}")
                new_link = DeviceUser(
                    device_id=device.id,
                    user_id=primary_user.id,
                    access_level='owner'
                )
                db.add(new_link)
                repaired_count += 1
            else:
                print(f"✅ Device {device.hostname} already linked.")

        if repaired_count > 0:
            await db.commit()
            print(f"✨ Successfully repaired {repaired_count} associations!")
        else:
            print("📭 No orphaned devices found.")
        
        break # Exit after one session

if __name__ == "__main__":
    asyncio.run(repair_associations())
