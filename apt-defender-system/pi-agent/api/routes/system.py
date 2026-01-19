"""
System API Routes - Pi system status and configuration
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
from api.auth import verify_user, UserTokenData
from database.db import get_db, Device, Threat, Scan, Action, DeviceUser
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
import psutil
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================
# API Endpoints
# ============================================

@router.get("/status")
async def get_system_status(token_data: UserTokenData = Depends(verify_user)):
    """Get Raspberry Pi system status"""
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "version": "1.0.0",
            "uptime_seconds": int(datetime.utcnow().timestamp() - psutil.boot_time()),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available // (1024 * 1024),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free // (1024 ** 3),
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@router.get("/alerts")
async def get_unread_alerts(
    db: AsyncSession = Depends(get_db),
    token_data: UserTokenData = Depends(verify_user)
):
    """Get unread alerts from threats and system events"""
    # Get active threats for user's devices
    result = await db.execute(
        select(Threat, Device.hostname)
        .join(Device, Threat.device_id == Device.id)
        .join(DeviceUser, Device.id == DeviceUser.device_id)
        .where(Threat.dismissed == False, DeviceUser.user_id == token_data.user_id)
        .order_by(desc(Threat.detected_at))
        .limit(10)
    )
    rows = result.all()
    
    alerts = []
    for threat, hostname in rows:
        alerts.append({
            "id": threat.id,
            "type": "threat",
            "severity": threat.severity,
            "message": f"{threat.type.replace('_', ' ').title()} detected on {hostname}",
            "timestamp": threat.detected_at.isoformat()
        })
    
    return {
        "success": True,
        "data": {
            "unread_count": len(alerts),
            "alerts": alerts
        }
    }

@router.get("/config")
async def get_configuration(token_data: UserTokenData = Depends(verify_user)):
    """Get current system configuration"""
    # TODO: Query config table
    
    return {
        "success": True,
        "data": {
            "scan_interval_hours": 24,
            "auto_quarantine": True,
            "alert_threshold_severity": 7,
            "cloud_sync_enabled": False,
            "network_ids_enabled": True
        }
    }

@router.put("/config")
async def update_configuration(
    config: Dict[str, Any],
    token_data: UserTokenData = Depends(verify_user)
):
    """Update system configuration"""
    # TODO: Validate config values
    # TODO: Update config table
    
    logger.info(f"Configuration updated: {config}")
    
    return {
        "success": True,
        "data": {
            "message": "Configuration updated successfully"
        }
    }

@router.get("/dashboard")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    token_data: UserTokenData = Depends(verify_user)
):
    """Get dashboard summary data with real metrics"""
    # Device counts (filtered by user)
    total_devices = await db.execute(
        select(func.count(Device.id))
        .join(DeviceUser, Device.id == DeviceUser.device_id)
        .where(DeviceUser.user_id == token_data.user_id)
    )
    online_devices = await db.execute(
        select(func.count(Device.id))
        .join(DeviceUser, Device.id == DeviceUser.device_id)
        .where(Device.status == 'online', DeviceUser.user_id == token_data.user_id)
    )
    
    # Threat counts (filtered by user)
    active_threats = await db.execute(
        select(func.count(Threat.id))
        .join(DeviceUser, Threat.device_id == DeviceUser.device_id)
        .where(Threat.dismissed == False, DeviceUser.user_id == token_data.user_id)
    )
    critical_threats = await db.execute(
        select(func.count(Threat.id))
        .join(DeviceUser, Threat.device_id == DeviceUser.device_id)
        .where(Threat.dismissed == False, Threat.severity >= 8, DeviceUser.user_id == token_data.user_id)
    )
    
    # Scans (filtered by user)
    scans_today = await db.execute(
        select(func.count(Scan.id))
        .join(DeviceUser, Scan.device_id == DeviceUser.device_id)
        .where(func.date(Scan.completed_at) == func.current_date(), DeviceUser.user_id == token_data.user_id)
    )
    
    # System info
    cpu_percent = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    
    return {
        "success": True,
        "data": {
            "devices": {
                "total": total_devices.scalar() or 0,
                "online": online_devices.scalar() or 0,
                "offline": (total_devices.scalar() or 0) - (online_devices.scalar() or 0),
                "with_threats": 0 # TODO: Calculate this
            },
            "threats": {
                "active": active_threats.scalar() or 0,
                "critical": critical_threats.scalar() or 0,
                "last_24h": 0 # TODO: Filter by time
            },
            "scans": {
                "completed_today": scans_today.scalar() or 0,
                "running": 0,
                "next_scheduled": None
            },
            "system_health": {
                "status": "healthy" if cpu_percent < 90 else "strained",
                "cpu_percent": cpu_percent,
                "memory_percent": mem.percent
            }
        }
    }
