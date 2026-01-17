"""
Actions API Routes - Execute response actions on devices
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from api.auth import verify_token, TokenData
from database.db import get_db, Device, Action
from connector.helper_client import HelperClient
from config.settings import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================
# Pydantic Models
# ============================================

class KillProcessRequest(BaseModel):
    pid: int

class QuarantineFileRequest(BaseModel):
    path: str
    reason: Optional[str] = "User initiated"

class ShutdownRequest(BaseModel):
    delay_seconds: int = 60

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
    return HelperClient(url)

# ============================================
# API Endpoints
# ============================================

@router.post("/devices/{device_id}/actions/kill")
async def kill_process(
    device_id: int,
    request: KillProcessRequest,
    token_data: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Kill a process on target device"""
    logger.warning(f"Process kill requested: Device {device_id}, PID {request.pid}")
    
    # Get client connected to device IP
    client = await get_device_client(device_id, db)
    
    # Execute command
    try:
        response = await client.kill_process(request.pid)
        result_status = "success" if response.get("success") else "failed"
    except Exception as e:
        logger.error(f"Failed to execute kill: {e}")
        result_status = "failed"
        
    return {
        "success": True,
        "data": {
            "action_id": 1, 
            "result": result_status
        }
    }

@router.post("/devices/{device_id}/actions/quarantine")
async def quarantine_file(
    device_id: int,
    request: QuarantineFileRequest,
    token_data: TokenData = Depends(verify_token)
):
    """Quarantine a file on target device"""
    logger.warning(f"File quarantine requested: Device {device_id}, Path {request.path}")
    
    # TODO: Call Helper service API
    # TODO: Move file to quarantine directory
    # TODO: Log action to database
    
    return {
        "success": True,
        "data": {
            "action_id": 2,
            "device_id": device_id,
            "action_type": "quarantine",
            "target": request.path,
            "result": "success",
            "quarantine_path": "/opt/apt-defender/quarantine/...",
            "reversible": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@router.post("/devices/{device_id}/actions/lock")
async def lock_device(device_id: int, token_data: TokenData = Depends(verify_token)):
    """Lock the target device screen"""
    logger.warning(f"Device lock requested: Device {device_id}")
    
    # TODO: Call Helper service API
    # TODO: Lock screen (Windows: LockWorkStation, Linux: loginctl lock-session)
    
    return {
        "success": True,
        "data": {
            "action_id": 3,
            "device_id": device_id,
            "action_type": "lock",
            "result": "success",
            "user_message": "Your computer has been locked for security",
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@router.post("/devices/{device_id}/actions/shutdown")
async def shutdown_device(
    device_id: int,
    request: ShutdownRequest,
    token_data: TokenData = Depends(verify_token)
):
    """Shutdown the target device"""
    logger.critical(f"Device shutdown requested: Device {device_id}")
    
    # TODO: Call Helper service API with delay
    # TODO: Allow user to cancel during delay period
    
    return {
        "success": True,
        "data": {
            "action_id": 4,
            "device_id": device_id,
            "action_type": "shutdown",
            "result": "pending",
            "delay_seconds": request.delay_seconds,
            "user_message": f"Computer will shutdown in {request.delay_seconds} seconds",
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@router.post("/devices/{device_id}/actions/isolate")
async def isolate_device(device_id: int, token_data: TokenData = Depends(verify_token)):
    """Disable network on target device"""
    logger.critical(f"Network isolation requested: Device {device_id}")
    
    # TODO: Call Helper service API
    # TODO: Disable all network adapters
    # TODO: Log action (this is reversible)
    
    return {
        "success": True,
        "data": {
            "action_id": 5,
            "device_id": device_id,
            "action_type": "isolate",
            "result": "success",
            "reversible": True,
            "user_message": "Network access has been disabled",
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@router.post("/devices/{device_id}/actions/restore-network")
async def restore_network(device_id: int, token_data: TokenData = Depends(verify_token)):
    """Re-enable network on target device"""
    logger.info(f"Network restore requested: Device {device_id}")
    
    # TODO: Call Helper service API
    # TODO: Re-enable network adapters
    
    return {
        "success": True,
        "data": {
            "action_id": 6,
            "device_id": device_id,
            "action_type": "restore_network",
            "result": "success",
            "user_message": "Network access restored",
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@router.get("/devices/{device_id}/actions/history")
async def get_action_history(
    device_id: int,
    limit: int = 50,
    token_data: TokenData = Depends(verify_token)
):
    """Get action history for device"""
    # TODO: Query actions table
    # TODO: Order by timestamp DESC
    
    return {
        "success": True,
        "data": {
            "actions": [
                {
                    "id": 1,
                    "timestamp": datetime.utcnow().isoformat(),
                    "action_type": "quarantine",
                    "target": "malware.exe",
                    "result": "success",
                    "initiated_by": "user_mobile"
                }
            ],
            "total": 1
        }
    }
