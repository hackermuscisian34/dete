import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from database.db import get_db, Device, init_database
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

async def list_devices(db: AsyncSession):
    result = await db.execute(select(Device))
    devices = result.scalars().all()
    if not devices:
        print("No devices found in database.")
        return []
    
    print(f"\nFound {len(devices)} devices:")
    print("-" * 60)
    print(f"{'ID':<5} {'Hostname':<20} {'IP Address':<15} {'Status':<10}")
    print("-" * 60)
    for d in devices:
        print(f"{d.id:<5} {d.hostname:<20} {d.ip_address or 'Unknown':<15} {d.status:<10}")
    print("-" * 60)
    return devices

async def delete_device(db: AsyncSession, device_id: int):
    # Verify device exists
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        print(f"❌ Device ID {device_id} not found.")
        return False
    
    # Confirm
    confirm = input(f"⚠️ Are you sure you want to delete device '{device.hostname}' (ID: {device.id})? This will delete all associated scans, threats, and logs. [y/N]: ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return False
        
    await db.delete(device)
    await db.commit()
    print(f"✅ Device {device_id} deleted successfully.")
    return True

async def delete_all_devices(db: AsyncSession):
    # Confirm
    confirm = input(f"⚠️ ⚠️ ⚠️ ARE YOU SURE YOU WANT TO DELETE ALL DEVICES? This cannot be undone. [y/N]: ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return False
    
    await db.execute(delete(Device))
    await db.commit()
    print(f"✅ All devices have been deleted.")
    return True

async def main():
    print("APT Defender - Device Management Tool")
    print("=====================================")
    
    # Initialize DB connection manually since we're a script
    async for db in get_db():
        devices = await list_devices(db)
        
        if not devices:
            return

        print("\nOptions:")
        print("1. Delete a specific device")
        print("2. Delete ALL devices")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ")
        
        if choice == '1':
            try:
                dev_id = int(input("Enter Device ID to delete: "))
                await delete_device(db, dev_id)
            except ValueError:
                print("Invalid input. Please enter a number.")
        elif choice == '2':
            await delete_all_devices(db)
        else:
            print("Exiting.")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAborted.")
