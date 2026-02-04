"""
Devices API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from api.auth import verify_user, UserTokenData
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db, Device, Threat, Scan, DeviceUser
from config.settings import settings
import logging
import sys
import importlib.util
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================
# Pydantic Models
# ============================================

class ScanRequest(BaseModel):
    scan_type: str = "full"  # full, quick, custom

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
        
        # 2. Try absolute path fallback (Foolproof for Pi env issues)
        try:
            # We are in api/routes/devices.py, base is 3 levels up
            base_dir = Path(__file__).parent.parent.parent
            client_path = base_dir / "connector" / "helper_client.py"
            
            if not client_path.exists():
                logger.error(f"HelperClient file not found at {client_path}")
                raise ImportError(f"Cannot find {client_path}")
                
            spec = importlib.util.spec_from_file_location("dynamic_connector.helper_client", str(client_path))
            module = importlib.util.module_from_spec(spec)
            sys.modules["dynamic_connector.helper_client"] = module
            spec.loader.exec_module(module)
            
            if hasattr(module, "HelperClient"):
                HelperClient = module.HelperClient
                logger.info("Successfully imported HelperClient via dynamic fallback")
            else:
                # Log what's actually in the module to help debugging
                logger.error(f"Module found but HelperClient missing! Contents: {dir(module)}")
                raise AttributeError("HelperClient not found in module")
        except Exception as fallback_err:
            logger.error(f"Fallback import also failed: {fallback_err}")
            raise HTTPException(status_code=500, detail="Internal system error: Component loading failed")

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

@router.get("")
async def list_devices(
    db: AsyncSession = Depends(get_db),
    token_data: UserTokenData = Depends(verify_user)
):
    """List all paired devices"""
    # Query devices associated with this user
    result = await db.execute(
        select(Device)
        .join(DeviceUser, Device.id == DeviceUser.device_id)
        .where(DeviceUser.user_id == token_data.user_id)
    )
    devices = result.scalars().all()
    
    device_list = []
    for device in devices:
        # Get active threat count
        threat_count = await db.execute(
            select(func.count(Threat.id))
            .where(Threat.device_id == device.id, Threat.dismissed == False)
        )
        
        # Get last scan
        last_scan = await db.execute(
            select(Scan.completed_at)
            .where(Scan.device_id == device.id, Scan.status == 'completed')
            .order_by(desc(Scan.completed_at))
            .limit(1)
        )
        
        device_list.append({
            "id": device.id,
            "hostname": device.hostname,
            "os": device.os,
            "os_version": device.os_version,
            "status": device.status,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "ip_address": device.ip_address,
            "active_threats": threat_count.scalar() or 0,
            "last_scan": last_scan.scalar().isoformat() if last_scan.scalar() else None
        })
    
    return {
        "success": True,
        "data": {
            "devices": device_list,
            "total": len(device_list)
        }
    }

@router.get("/{device_id}")
async def get_device(
    device_id: int, 
    db: AsyncSession = Depends(get_db),
    token_data: UserTokenData = Depends(verify_user)
):
    """Get detailed device information"""
    # Verify user association
    association = await db.execute(
        select(DeviceUser).where(DeviceUser.device_id == device_id, DeviceUser.user_id == token_data.user_id)
    )
    if not association.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to this device")

    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get stats
    threat_count = await db.execute(select(func.count(Threat.id)).where(Threat.device_id == device_id, Threat.dismissed == False))
    total_found = await db.execute(select(func.count(Threat.id)).where(Threat.device_id == device_id))
    scan_count = await db.execute(select(func.count(Scan.id)).where(Scan.device_id == device_id))
    
    return {
        "success": True,
        "data": {
            "id": device.id,
            "hostname": device.hostname,
            "os": device.os,
            "os_version": device.os_version,
            "status": device.status,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "ip_address": device.ip_address,
            "helper_version": device.helper_version,
            "paired_at": device.paired_at.isoformat() if device.paired_at else None,
            "total_scans": scan_count.scalar() or 0,
            "active_threats": threat_count.scalar() or 0,
            "total_threats_detected": total_found.scalar() or 0
        }
    }

@router.post("/{device_id}/scan")
async def trigger_scan(
    device_id: int,
    request: ScanRequest,
    token_data: UserTokenData = Depends(verify_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger a security scan on device"""
    # Verify user association
    association = await db.execute(
        select(DeviceUser).where(DeviceUser.device_id == device_id, DeviceUser.user_id == token_data.user_id)
    )
    if not association.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to this device")

    try:
        client = await get_device_client(device_id, db)
        # Start scan on helper service
        result = await client.start_scan(request.scan_type)
        
        # Create scan record in database
        new_scan = Scan(
            device_id=device_id,
            scan_type=request.scan_type,
            status='running'
        )
        db.add(new_scan)
        await db.commit()
        await db.refresh(new_scan)
        
        return {
            "success": True,
            "data": {
                "scan_id": new_scan.id,
                "status": "running",
                "started_at": new_scan.started_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to trigger scan on device {device_id}: {e}")
        # If it's already an HTTPException, re-raise it
        if isinstance(e, HTTPException):
            raise e
        if type(e).__name__ == "HelperTLSConfigurationError":
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to reach device: {str(e)}")

@router.get("/{device_id}/scan/status")
async def get_scan_status(
    device_id: int,
    token_data: UserTokenData = Depends(verify_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the latest scan status from the device"""
    # Verify user association
    association = await db.execute(
        select(DeviceUser).where(DeviceUser.device_id == device_id, DeviceUser.user_id == token_data.user_id)
    )
    if not association.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to this device")

    try:
        # Get latest scan from DB
        result = await db.execute(
            select(Scan).where(Scan.device_id == device_id).order_by(desc(Scan.started_at)).limit(1)
        )
        db_scan = result.scalar_one_or_none()
        
        if not db_scan:
            return {"success": True, "data": None}

        # If it's running, poll the helper service for latest progress
        if db_scan.status == 'running':
            try:
                client = await get_device_client(device_id, db)
                helper_status = await client.get_scan_status()
                
                if helper_status.get('success'):
                    status_data = helper_status.get('data', {})
                    # Update DB record
                    db_scan.files_checked = status_data.get('scanned_files', 0)
                    db_scan.total_files = status_data.get('total_files', 0)
                    db_scan.threats_found = status_data.get('threats_found', 0)
                    
                    if not status_data.get('active'):
                        db_scan.status = 'completed'
                        db_scan.completed_at = datetime.utcnow()
                    
                    await db.commit()
            except Exception as poll_err:
                logger.warning(f"Failed to poll scan status for device {device_id}: {poll_err}")

        # Calculate time estimation (very basic: linear extrapolation)
        estimated_remaining_seconds = 0
        if db_scan.status == 'running' and db_scan.files_checked > 0 and db_scan.total_files > 0:
            elapsed = (datetime.utcnow() - db_scan.started_at).total_seconds()
            rate = db_scan.files_checked / elapsed
            remaining_files = db_scan.total_files - db_scan.files_checked
            if rate > 0:
                estimated_remaining_seconds = int(remaining_files / rate)

        return {
            "success": True,
            "data": {
                "scan_id": db_scan.id,
                "status": db_scan.status,
                "files_checked": db_scan.files_checked,
                "total_files": db_scan.total_files,
                "threats_found": db_scan.threats_found,
                "started_at": db_scan.started_at.isoformat(),
                "remaining_seconds": estimated_remaining_seconds
            }
        }
    except Exception as e:
        logger.error(f"Error getting scan status for device {device_id}: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{device_id}/processes")
async def get_processes(
    device_id: int, 
    token_data: UserTokenData = Depends(verify_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current running processes from device"""
    # Verify user association
    association = await db.execute(
        select(DeviceUser).where(DeviceUser.device_id == device_id, DeviceUser.user_id == token_data.user_id)
    )
    if not association.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to this device")

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
        if isinstance(e, HTTPException):
            raise e
        if type(e).__name__ == "HelperTLSConfigurationError":
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to reach device: {str(e)}")

@router.get("/{device_id}/connections")
async def get_connections(
    device_id: int, 
    token_data: UserTokenData = Depends(verify_user),
    db: AsyncSession = Depends(get_db)
):
    """Get active network connections from device"""
    # Verify user association
    association = await db.execute(
        select(DeviceUser).where(DeviceUser.device_id == device_id, DeviceUser.user_id == token_data.user_id)
    )
    if not association.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to this device")

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
        if isinstance(e, HTTPException):
            raise e
        if type(e).__name__ == "HelperTLSConfigurationError":
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to reach device: {str(e)}")

@router.get("/{device_id}/timeline")
async def get_forensic_timeline(
    device_id: int,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    token_data: UserTokenData = Depends(verify_user)
):
    """Get forensic timeline for device"""
    # Verify user association
    association = await db.execute(
        select(DeviceUser).where(DeviceUser.device_id == device_id, DeviceUser.user_id == token_data.user_id)
    )
    if not association.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to this device")

    from database.db import ForensicTimeline
    result = await db.execute(
        select(ForensicTimeline)
        .where(ForensicTimeline.device_id == device_id)
        .order_by(desc(ForensicTimeline.timestamp))
        .limit(limit)
    )
    events = result.scalars().all()
    
    return {
        "success": True,
        "data": {
            "events": [
                {
                    "id": e.id,
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "details": e.details,
                    "source": e.source,
                    "severity": e.severity
                } for e in events
            ],
            "total": len(events)
        }
    }

@router.get("/{device_id}/scan/{scan_id}/report")
async def get_scan_report(
    device_id: int,
    scan_id: int,
    token_data: UserTokenData = Depends(verify_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a security report for a specific scan"""
    # Verify user association
    association = await db.execute(
        select(DeviceUser).where(DeviceUser.device_id == device_id, DeviceUser.user_id == token_data.user_id)
    )
    if not association.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to this device")

    # Get scan and device details
    result = await db.execute(select(Scan).where(Scan.id == scan_id, Scan.device_id == device_id))
    db_scan = result.scalar_one_or_none()
    
    if not db_scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    # Generate HTML report
    html_content = f"""
    <html>
    <head>
        <title>Security Scan Report - {device.hostname}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 40px auto; padding: 20px; }}
            .header {{ background: #2ecc71; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ border: 1px solid #ddd; padding: 20px; border-radius: 0 0 8px 8px; }}
            .stat-box {{ display: inline-block; width: 30%; background: #f9f9f9; padding: 15px; margin: 10px 1%; border-radius: 5px; box-sizing: border-box; text-align: center; }}
            .danger {{ color: #e74c3c; font-weight: bold; }}
            .success {{ color: #2ecc71; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Security Scan Report</h1>
            <p>Device: <strong>{device.hostname}</strong> ({device.ip_address})</p>
        </div>
        <div class="content">
            <h2>Summary</h2>
            <div class="stat-box">
                <p>Status</p>
                <p class="{'success' if db_scan.status == 'completed' else ''}"><strong>{db_scan.status.upper()}</strong></p>
            </div>
            <div class="stat-box">
                <p>Files Checked</p>
                <p><strong>{db_scan.files_checked}</strong></p>
            </div>
            <div class="stat-box">
                <p>Threats Found</p>
                <p class="{'danger' if db_scan.threats_found > 0 else 'success'}"><strong>{db_scan.threats_found}</strong></p>
            </div>

            <h2>Details</h2>
            <table>
                <tr><th>Scan ID</th><td>{db_scan.id}</td></tr>
                <tr><th>Scan Type</th><td>{db_scan.scan_type}</td></tr>
                <tr><th>Started At</th><td>{db_scan.started_at.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                <tr><th>Completed At</th><td>{db_scan.completed_at.strftime('%Y-%m-%d %H:%M:%S') if db_scan.completed_at else 'N/A'}</td></tr>
                <tr><th>OS</th><td>{device.os} {device.os_version or ''}</td></tr>
            </table>

            <h2>Verdict</h2>
            <p>
                { "⚠️ ACTION REQUIRED: Several suspicious items were detected. Please review the 'Threats' section in the mobile app." if db_scan.threats_found > 0 
                  else "✅ CLEAN: No known threats were detected during this scan. Your device is protected." }
            </p>
        </div>
        <div style="text-align: center; margin-top: 20px; color: #888; font-size: 0.8em;">
            Generated by APT Defender System V2.0
        </div>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

@router.get("/{device_id}/scan/{scan_id}/report/log")
async def get_scan_report_log(
    device_id: int,
    scan_id: int,
    token_data: UserTokenData = Depends(verify_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a plain text log report for a specific scan"""
    # Verify user association
    association = await db.execute(
        select(DeviceUser).where(DeviceUser.device_id == device_id, DeviceUser.user_id == token_data.user_id)
    )
    if not association.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to this device")

    # Get scan and device details
    result = await db.execute(select(Scan).where(Scan.id == scan_id, Scan.device_id == device_id))
    db_scan = result.scalar_one_or_none()
    
    if not db_scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    log_content = f"""
APT DEFENDER SECURITY SCAN LOG
==============================
Device: {device.hostname}
IP Address: {device.ip_address}
OS: {device.os} {device.os_version or ''}
------------------------------
Scan ID: {db_scan.id}
Scan Type: {db_scan.scan_type}
Status: {db_scan.status.upper()}
Started At: {db_scan.started_at.strftime('%Y-%m-%d %H:%M:%S')}
Completed At: {db_scan.completed_at.strftime('%Y-%m-%d %H:%M:%S') if db_scan.completed_at else 'N/A'}
------------------------------
FILES CHECKED: {db_scan.files_checked}
THREATS FOUND: {db_scan.threats_found}
------------------------------
VERDICT:
{ '⚠️ ACTION REQUIRED: Suspicious items detected.' if db_scan.threats_found > 0 else '✅ CLEAN: No threats detected.' }
==============================
Generated by APT Defender System V2.0
"""
    
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=log_content.strip())

@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    token_data: UserTokenData = Depends(verify_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a device and its associations"""
    # Verify user association and ownership/access
    association = await db.execute(
        select(DeviceUser).where(DeviceUser.device_id == device_id, DeviceUser.user_id == token_data.user_id)
    )
    assoc = association.scalar_one_or_none()
    if not assoc:
        raise HTTPException(status_code=403, detail="Access denied to this device")
        
    if assoc.access_level != 'owner':
        raise HTTPException(status_code=403, detail="Only owners can delete devices")

    # Delete the device (CASCADE will handle device_users and other related tables if set up)
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    await db.delete(device)
    await db.commit()
    
    logger.info(f"User {token_data.user_id} deleted device {device_id}")
    
    return {"success": True, "message": "Device deleted successfully"}
