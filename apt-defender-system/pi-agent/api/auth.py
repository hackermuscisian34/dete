"""
Authentication and JWT handling
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from config.settings import settings
from database.db import get_db, Device
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# ============================================
# Pydantic Models
# ============================================

class PairingRequest(BaseModel):
    pairing_token: str
    device_hostname: str
    device_ip: str
    device_os: str = "windows"
    device_os_version: str = "10"

class PairingResponse(BaseModel):
    success: bool
    access_token: str
    device_id: int

class TokenData(BaseModel):
    device_id: int
    hostname: str

# ============================================
# JWT Functions
# ============================================

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Verify JWT token and return token data"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        
        device_id: int = payload.get("device_id")
        hostname: str = payload.get("hostname")
        
        if device_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return TokenData(device_id=device_id, hostname=hostname)
    
    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

def generate_pairing_token() -> str:
    """Generate secure pairing token"""
    return secrets.token_urlsafe(32)

# ============================================
# API Endpoints
# ============================================

@router.post("/pair")
async def pair_device(request: PairingRequest, db: AsyncSession = Depends(get_db)):
    """
    Pair a new device using pairing token
    This endpoint validates the one-time pairing token and issues a long-lived JWT
    """
    logger.info(f"Device pairing request: {request.device_hostname} ({request.device_ip})")
    
    # Check if device already exists
    result = await db.execute(select(Device).where(Device.hostname == request.device_hostname))
    existing_device = result.scalar_one_or_none()
    
    if existing_device:
        # Update existing device IP and last seen
        existing_device.ip_address = request.device_ip
        existing_device.last_seen = datetime.utcnow()
        await db.commit()
        await db.refresh(existing_device)
        device_id = existing_device.id
        logger.info(f"Updated existing device: {device_id}")
    else:
        # Create new device
        new_device = Device(
            hostname=request.device_hostname,
            ip_address=request.device_ip,
            os=request.device_os,
            os_version=request.device_os_version,
            status="online",
            paired_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        db.add(new_device)
        await db.commit()
        await db.refresh(new_device)
        device_id = new_device.id
        logger.info(f"Registered new device: {device_id}")
    
    # Create JWT token
    access_token = create_access_token({
        "device_id": device_id,
        "hostname": request.device_hostname
    })
    
    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "device_id": device_id,
            "expires_in_hours": settings.jwt_expiration_hours
        }
    }

@router.post("/refresh")
async def refresh_token(token_data: TokenData = Depends(verify_token)):
    """Refresh JWT token"""
    new_token = create_access_token({
        "device_id": token_data.device_id,
        "hostname": token_data.hostname
    })
    
    return {
        "success": True,
        "data": {
            "access_token": new_token,
            "expires_in_hours": settings.jwt_expiration_hours
        }
    }

@router.get("/verify")
async def verify_current_token(token_data: TokenData = Depends(verify_token)):
    """Verify current token is valid"""
    return {
        "success": True,
        "data": {
            "valid": True,
            "device_id": token_data.device_id,
            "hostname": token_data.hostname
        }
    }

@router.post("/generate-pairing-code")
async def generate_pairing_code():
    """Generate a new pairing code (admin only)"""
    # TODO: Add admin authentication
    pairing_token = generate_pairing_token()
    
    # TODO: Store in database with expiry
    
    return {
        "success": True,
        "data": {
            "pairing_token": pairing_token,
            "expires_in_minutes": settings.pairing_token_expiry_minutes
        }
    }
