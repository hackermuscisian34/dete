"""
Actions API Routes - Execute response actions on devices
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from api.auth import verify_user, UserTokenData
from database.db import get_db, Device, Action
from config.settings import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import sys
import importlib.util
from pathlib import Path

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

async def get_device_client(device_id: int, db: AsyncSession):
    """Get initialized HelperClient for a device"""
    # 1. Try standard import
    try:
        from connector.helper_client import HelperClient
        logger.info("Successfully imported HelperClient via standard import")
    except (ImportError, AttributeError) as e:
        logger.warning(f"Standard import failed for HelperClient: {e}. Trying fallback...")
        
        # 2. Try absolute path fallback
        try:
            base_dir = Path(__file__).parent.parent.parent
            client_path = base_dir / "connector" / "helper_client.py"
            
            if not client_path.exists():
                raise ImportError(f"Cannot find {client_path}")
                
            spec = importlib.util.spec_from_file_location("dynamic_actions.helper_client", str(client_path))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "HelperClient"):
                HelperClient = module.HelperClient
            else:
                raise AttributeError("HelperClient not found in module")
        except Exception as fallback_err:
            logger.error(f"Fallback import also failed for Actions: {fallback_err}")
            raise HTTPException(status_code=500, detail="Internal system error: Action component load failed")

    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    if not device.ip_address:
        raise HTTPException(status_code=400, detail="Device has no IP address")

    # Construct secure URL using the IP from database
    url = f"https://{device.ip_address}:{settings.helper_port}"
    cert_path = settings.helper_client_cert_path or None
    key_path = settings.helper_client_key_path or None
    ca_cert_path = settings.helper_ca_cert_path or None
    return HelperClient(
        url,
        cert_path=cert_path,
        key_path=key_path,
        ca_cert_path=ca_cert_path,
        verify_tls=settings.helper_tls_verify,
    )

# ============================================
# API Endpoints
# ============================================

@router.post("/devices/{device_id}/actions/kill")
async def kill_process(
    device_id: int,
    request: KillProcessRequest,
    token_data: UserTokenData = Depends(verify_user),
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
        if type(e).__name__ == "HelperTLSConfigurationError":
            raise HTTPException(status_code=503, detail=str(e))
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
    token_data: UserTokenData = Depends(verify_user)
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
async def lock_device(device_id: int, token_data: UserTokenData = Depends(verify_user)):
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
    token_data: UserTokenData = Depends(verify_user)
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
async def isolate_device(device_id: int, token_data: UserTokenData = Depends(verify_user)):
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
async def restore_network(device_id: int, token_data: UserTokenData = Depends(verify_user)):
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
    token_data: UserTokenData = Depends(verify_user)
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
