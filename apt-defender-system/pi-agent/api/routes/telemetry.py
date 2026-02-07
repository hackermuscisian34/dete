"""
Device telemetry routes - Fetch system telemetry from monitored PCs
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
import logging
from database.db import get_db_manager
from connector.helper_client import HelperClient, HelperServiceUnavailableError
from api.auth import verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/devices/{device_id}/telemetry")
async def get_device_telemetry(
    device_id: str,
    _: str = Depends(verify_api_key)
) -> Dict:
    """
    Fetch real-time system telemetry from a monitored PC
    
    Returns:
        - CPU usage (percent, cores)
        - Memory usage (total, used, available in MB)
        - Disk usage (total, used, free in GB)
        - System info (hostname, OS, uptime)
    """
    db = get_db_manager()
    
    # Get device info from database
    device = await db.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if not device.get("ip_address"):
        raise HTTPException(status_code=400, detail="Device has no IP address")
    
    # Build helper service URL
    helper_url = f"http://{device['ip_address']}:7890"
    
    try:
        # Create helper client and fetch telemetry
        client = HelperClient(helper_url)
        telemetry_data = await client.get_telemetry()
        
        return {
            "success": True,
            "device_id": device_id,
            "device_name": device.get("device_name", "Unknown"),
            "telemetry": telemetry_data
        }
    
    except HelperServiceUnavailableError as e:
        logger.error(f"Helper service unavailable for device {device_id}: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to PC helper service: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching telemetry for device {device_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch telemetry: {str(e)}"
        )


@router.get("/devices/{device_id}/telemetry/stream")
async def stream_device_telemetry(
    device_id: str,
    _: str = Depends(verify_api_key)
):
    """
    Stream real-time telemetry updates (for future WebSocket support)
    Currently returns the same as /telemetry
    """
    # For now, just return regular telemetry
    # Can be upgraded to SSE or WebSocket in the future
    return await get_device_telemetry(device_id, _)
