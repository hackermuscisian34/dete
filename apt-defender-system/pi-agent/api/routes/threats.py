"""
Threats API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from api.auth import verify_user, UserTokenData
from database.db import get_db, Threat, Device, DeviceUser
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================
# Pydantic Models
# ============================================

class ThreatResponse(BaseModel):
    id: int
    device_id: int
    device_hostname: str
    detected_at: datetime
    severity: int
    type: str
    indicator: str
    explanation: str
    recommended_action: str
    action_taken: Optional[str]
    dismissed: bool

class DismissThreatRequest(BaseModel):
    reason: str

# ============================================
# API Endpoints
# ============================================

@router.get("")
async def list_threats(
    device_id: Optional[int] = None,
    dismissed: bool = False,
    min_severity: int = 1,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    token_data: UserTokenData = Depends(verify_user)
):
    """List threats across all devices or specific device"""
    query = select(Threat, Device.hostname).join(Device, Threat.device_id == Device.id)
    
    # Filter by user association
    query = query.join(DeviceUser, Device.id == DeviceUser.device_id).where(DeviceUser.user_id == token_data.user_id)
    
    if device_id:
        query = query.where(Threat.device_id == device_id)
    
    query = query.where(Threat.dismissed == dismissed)
    query = query.where(Threat.severity >= min_severity)
    query = query.order_by(desc(Threat.detected_at)).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    threats = []
    for threat, hostname in rows:
        threats.append({
            "id": threat.id,
            "device_id": threat.device_id,
            "device_hostname": hostname,
            "detected_at": threat.detected_at.isoformat(),
            "severity": threat.severity,
            "type": threat.type,
            "indicator": threat.indicator,
            "explanation": threat.explanation,
            "recommended_action": threat.recommended_action,
            "action_taken": threat.action_taken,
            "dismissed": threat.dismissed
        })
    
    return {
        "success": True,
        "data": {
            "threats": threats,
            "total": len(threats)
        }
    }

@router.get("/{threat_id}")
async def get_threat(
    threat_id: int, 
    db: AsyncSession = Depends(get_db),
    token_data: UserTokenData = Depends(verify_user)
):
    """Get detailed threat information"""
    query = (
        select(Threat, Device.hostname)
        .join(Device, Threat.device_id == Device.id)
        .join(DeviceUser, Device.id == DeviceUser.device_id)
        .where(Threat.id == threat_id, DeviceUser.user_id == token_data.user_id)
    )
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Threat not found or access denied")
    
    threat, hostname = row
    import json
    evidence = json.loads(threat.evidence) if threat.evidence else {}
    
    return {
        "success": True,
        "data": {
            "id": threat.id,
            "device_id": threat.device_id,
            "device_hostname": hostname,
            "detected_at": threat.detected_at.isoformat(),
            "severity": threat.severity,
            "type": threat.type,
            "indicator": threat.indicator,
            "hash_value": threat.hash_value,
            "explanation": threat.explanation,
            "recommended_action": threat.recommended_action,
            "action_taken": threat.action_taken,
            "dismissed": threat.dismissed,
            "evidence": evidence
        }
    }

@router.post("/{threat_id}/dismiss")
async def dismiss_threat(
    threat_id: int,
    request: DismissThreatRequest,
    token_data: UserTokenData = Depends(verify_user)
):
    """Mark threat as false positive / dismissed"""
    logger.info(f"Threat {threat_id} dismissed: {request.reason}")
    
    # Cloud sync
    # In a real implementation we would fetch the device hostname first
    # This is a placeholder for where the sync call goes
    # await cloud_sync.push_threat("HOSTNAME_HERE", {"type": "dismissal", "id": threat_id})
    
    # TODO: Update threat record
    # TODO: Set dismissed = TRUE, dismissed_at = NOW
    
    return {
        "success": True,
        "data": {
            "message": "Threat dismissed successfully"
        }
    }

@router.get("/stats/summary")
async def get_threat_stats(token_data: UserTokenData = Depends(verify_user)):
    """Get threat statistics summary"""
    # TODO: Aggregate threat data
    # TODO: Group by severity, type, device
    
    return {
        "success": True,
        "data": {
            "total_threats": 25,
            "active_threats": 3,
            "critical_threats": 1,
            "threats_by_type": {
                "malware": 10,
                "apt": 5,
                "persistence": 6,
                "network": 4
            },
            "threats_last_24h": 2
        }
    }
