"""
Devices API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from api.auth import verify_token, TokenData
from connector.supabase_client import cloud_sync
from connector.helper_client import HelperClient
from database.db import get_db, Device
from config.settings import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================
# Pydantic Models
# ============================================

class DeviceResponse(BaseModel):
    id: int
    hostname: str
    os: str
    os_version: Optional[str]
    status: str
    last_seen: datetime
    ip_address: Optional[str]
    active_threats: int
    last_scan: Optional[datetime]

class ScanRequest(BaseModel):
    scan_type: str = "full"  # full, quick, custom

# ============================================
# Helpers
# ============================================

async def get_device_client(device_id: int, db: AsyncSession) -> HelperClient:
    """Get initialized HelperClient for a device"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    if not device.ip_address:
        raise HTTPException(status_code=400, detail="Device has no IP address")

    # Construct secure URL using the IP from database
    url = f"https://{device.ip_address}:{settings.helper_port}"
    # Pass SSL certs from settings for mTLS
    return HelperClient(url, cert_path=settings.ssl_certfile)

# ============================================
# API Endpoints
# ============================================

@router.get("")
async def list_devices(token_data: TokenData = Depends(verify_token)):
    """List all paired devices"""
    # TODO: Query database for all devices
    # TODO: Include threat counts and last scan info
    
    return {
        "success": True,
        "data": {
            "devices": [
                {
                    "id": 1,
                    "hostname": "LAPTOP-001",
                    "os": "windows",
                    "os_version": "Windows 11",
                    "status": "online",
                    "last_seen": datetime.utcnow().isoformat(),
                    "ip_address": "192.168.1.100",
                    "active_threats": 0,
                    "last_scan": datetime.utcnow().isoformat()
                }
            ],
            "total": 1
        }
    
    # Background sync (fire and forget)
    # await cloud_sync.sync_device_status("LAPTOP-001", "online", "192.168.1.100", "windows")
    }

@router.get("/{device_id}")
async def get_device(device_id: int, token_data: TokenData = Depends(verify_token)):
    """Get detailed device information"""
    # TODO: Query database for device details
    # TODO: Include recent threats, scans, and actions
    
    return {
        "success": True,
        "data": {
            "id": device_id,
            "hostname": "LAPTOP-001",
            "os": "windows",
            "os_version": "Windows 11",
            "status": "online",
            "last_seen": datetime.utcnow().isoformat(),
            "ip_address": "192.168.1.100",
            "helper_version": "1.0.0",
            "paired_at": datetime.utcnow().isoformat(),
            "total_scans": 15,
            "active_threats": 0,
            "total_threats_detected": 3
        }
    }

@router.post("/{device_id}/scan")
async def trigger_scan(
    device_id: int,
    request: ScanRequest,
    token_data: TokenData = Depends(verify_token)
):
    """Trigger a security scan on device"""
    logger.info(f"Scan requested for device {device_id}: {request.scan_type}")
    
    # TODO: Create scan record in database
    # TODO: Dispatch scan task to background worker
    # TODO: Connect to Helper service to collect data
    
    return {
        "success": True,
        "data": {
            "scan_id": 123,
            "device_id": device_id,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "estimated_duration_minutes": 15
        }
    }

@router.delete("/{device_id}")
async def unpair_device(device_id: int, token_data: TokenData = Depends(verify_token)):
    """Unpair a device"""
    logger.warning(f"Device {device_id} unpair requested")
    
    # TODO: Delete device from database
    # TODO: Revoke certificates
    # TODO: Clean up quarantine files
    
    return {
        "success": True,
        "data": {
            "message": "Device unpaired successfully"
        }
    }

@router.get("/{device_id}/processes")
async def get_processes(
    device_id: int, 
    token_data: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get current running processes from device"""
    try:
        # Get client connected to device
        client = await get_device_client(device_id, db)
        
        # specific endpoint on helper is /v1/processes
        processes = await client.get_processes()
        
        return {
            "success": True,
            "data": {
                "processes": processes,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to fetch processes from device {device_id}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to reach device: {str(e)}")

@router.get("/{device_id}/connections")
async def get_connections(
    device_id: int, 
    token_data: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get active network connections from device"""
    try:
        # Get client connected to device
        client = await get_device_client(device_id, db)
        
        connections = await client.get_network_connections()
        
        return {
            "success": True,
            "data": {
                "connections": connections,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to fetch connections from device {device_id}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to reach device: {str(e)}")

@router.get("/{device_id}/timeline")
async def get_forensic_timeline(
    device_id: int,
    limit: int = 100,
    token_data: TokenData = Depends(verify_token)
):
    """Get forensic timeline for device"""
    # TODO: Query forensic_timeline table
    # TODO: Order by timestamp DESC
    
    return {
        "success": True,
        "data": {
            "events": [
                {
                    "id": 1,
                    "timestamp": datetime.utcnow().isoformat(),
                    "event_type": "process_created",
                    "details": "powershell.exe spawned by cmd.exe",
                    "source": "process_monitor",
                    "severity": 5
                }
            ],
            "total": 1
        }
    }
