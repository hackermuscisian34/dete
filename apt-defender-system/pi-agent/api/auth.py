"""
Authentication and JWT handling
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import bcrypt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from config.settings import settings
from database.db import get_db, Device, User, PairingToken, DeviceUser
from sqlalchemy import select, func
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

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PairingResponse(BaseModel):
    success: bool
    access_token: str
    device_id: int

class TokenData(BaseModel):
    device_id: int
    hostname: str

class UserTokenData(BaseModel):
    user_id: int
    email: str
    role: str

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

def verify_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserTokenData:
    """Verify User JWT token and return user data"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        role: str = payload.get("role")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication credentials"
            )
        
        return UserTokenData(user_id=user_id, email=email, role=role)
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

def verify_user_from_query(token: str = Query(..., description="JWT Token")) -> UserTokenData:
    """Verify User JWT token from query parameter"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        role: str = payload.get("role")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication credentials"
            )
        
        return UserTokenData(user_id=user_id, email=email, role=role)
    
    except JWTError as e:
        logger.error(f"User JWT validation error (query param): {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

def generate_pairing_token() -> str:
    """Generate a short, easy-to-type pairing token (8 chars)"""
    import string
    alphabet = string.ascii_uppercase + string.digits
    # Exclude confusing characters like O, 0, I, 1
    safe_alphabet = ''.join(c for c in alphabet if c not in '0O1I')
    return ''.join(secrets.choice(safe_alphabet) for _ in range(8))

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a hashed password using bcrypt"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

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
    
    # Validate pairing token
    token = request.pairing_token.strip()
    logger.debug(f"DEBUG: Validating token: '{token}'")
    
    result = await db.execute(
        select(PairingToken)
        .where(PairingToken.token == token)
    )
    token_entries = result.scalars().all()
    logger.debug(f"DEBUG: Found {len(token_entries)} matching tokens")
    
    token_entry = None
    for t in token_entries:
        if t.used_at is None:
            token_entry = t
            break
            
    if not token_entry:
        logger.warning(f"Pairing failed: Token invalid or already used. Token sent: {request.pairing_token}")
        raise HTTPException(status_code=400, detail="Invalid or already used pairing token")
    
    now = datetime.utcnow()
    logger.debug(f"DEBUG: Current time: {now}, Token expires at: {token_entry.expires_at}")
    if token_entry.expires_at < now:
        logger.warning(f"Pairing failed: Token expired. Expiry: {token_entry.expires_at}, Now: {now}")
        raise HTTPException(status_code=400, detail="Pairing token has expired")
    
    # Check if device already exists
    result = await db.execute(select(Device).where(Device.hostname == request.device_hostname))
    existing_device = result.scalar_one_or_none()
    
    if existing_device:
        # Update existing device IP and last seen
        existing_device.ip_address = request.device_ip
        existing_device.last_seen = datetime.utcnow()
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
        await db.flush() # Get ID
        device_id = new_device.id
        logger.info(f"Registered new device: {device_id}")
    
    # Mark token as used
    token_entry.used_at = datetime.utcnow()
    
    # Link device to user if not already linked
    result = await db.execute(
        select(DeviceUser)
        .where(DeviceUser.device_id == device_id, DeviceUser.user_id == token_entry.created_by)
    )
    existing_link = result.scalar_one_or_none()
    
    if not existing_link:
        new_link = DeviceUser(
            device_id=device_id,
            user_id=token_entry.created_by,
            access_level='owner'
        )
        db.add(new_link)
        logger.info(f"Linked device {device_id} to user {token_entry.created_by}")
    
    await db.commit()
    
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
async def generate_pairing_code(
    db: AsyncSession = Depends(get_db),
    token_data: UserTokenData = Depends(verify_user)
):
    """Generate a new pairing code (user required)"""
    pairing_token = generate_pairing_token()
    
    # Store in database
    expires_at = datetime.utcnow() + timedelta(minutes=settings.pairing_token_expiry_minutes)
    token_entry = PairingToken(
        token=pairing_token,
        expires_at=expires_at,
        created_by=token_data.user_id
    )
    db.add(token_entry)
    await db.commit()
    
    return {
        "success": True,
        "data": {
            "pairing_token": pairing_token,
            "expires_in_minutes": settings.pairing_token_expiry_minutes
        }
    }

@router.post("/register")
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    new_user = User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        role='admin' if (await db.execute(select(func.count(User.id)))).scalar() == 0 else 'user'
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {"success": True, "message": "User registered successfully"}

@router.post("/login")
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get access token"""
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create JWT
    access_token = create_access_token({
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    })
    
    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role
            }
        }
    }

@router.post("/register-device-manual")
async def register_device_manual(
    device_ip: str,
    device_hostname: str,
    device_os: str = "windows",
    device_os_version: str = "10",
    db: AsyncSession = Depends(get_db),
    token_data: UserTokenData = Depends(verify_user)
):
    """
    Manually register a PC by IP address (no pairing code needed)
    Used when mobile app knows the PC's IP and wants to add it directly
    """
    logger.info(f"Manual device registration: {device_hostname} ({device_ip}) by user {token_data.user_id}")
    
    # Check if device already exists for this user
    from connector.helper_client import HelperClient, HelperServiceUnavailableError
    
    # Try to contact the PC first to verify it's reachable
    try:
        helper_url = f"http://{device_ip}:7890"
        client = HelperClient(helper_url)
        health = await client.health_check()
        
        if not health.get('success'):
            raise HTTPException(status_code=503, detail="PC helper service is not responding")
            
    except HelperServiceUnavailableError:
        raise HTTPException(
            status_code=503, 
            detail=f"Cannot reach PC at {device_ip}. Make sure the Helper Service is running."
        )
    except Exception as e:
        logger.error(f"Failed to verify PC connectivity: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to PC: {str(e)}"
        )
    
    # Check if device already exists by hostname or IP
    result = await db.execute(
        select(Device).where(
            (Device.hostname == device_hostname) | (Device.ip_address == device_ip)
        )
    )
    existing_device = result.scalar_one_or_none()
    
    if existing_device:
        # Update existing device
        existing_device.ip_address = device_ip
        existing_device.hostname = device_hostname
        existing_device.os = device_os
        existing_device.os_version = device_os_version
        existing_device.last_seen = datetime.utcnow()
        existing_device.status = "online"
        device_id = existing_device.id
        logger.info(f"Updated existing device: {device_id}")
    else:
        # Create new device
        new_device = Device(
            hostname=device_hostname,
            ip_address=device_ip,
            os=device_os,
            os_version=device_os_version,
            status="online",
           paired_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        db.add(new_device)
        await db.flush()
        device_id = new_device.id
        logger.info(f"Registered new device: {device_id}")
    
    # Link device to user if not already linked
    result = await db.execute(
        select(DeviceUser).where(
            DeviceUser.device_id == device_id,
            DeviceUser.user_id == token_data.user_id
        )
    )
    existing_link = result.scalar_one_or_none()
    
    if not existing_link:
        new_link = DeviceUser(
            device_id=device_id,
            user_id=token_data.user_id,
            access_level='owner'
        )
        db.add(new_link)
        logger.info(f"Linked device {device_id} to user {token_data.user_id}")
    
    await db.commit()
    
    # Notify the PC that it has been registered with this Pi Agent
    try:
        import httpx
        import socket
        
        # Get this Pi's IP address (best guess - first non-loopback)
        pi_ip = socket.gethostbyname(socket.gethostname())
        
        notification_url = f"http://{device_ip}:7890/api/v1/register-notification"
        async with httpx.AsyncClient(timeout=5.0) as notify_client:
            await notify_client.post(
                notification_url,
                json={
                    "pi_agent_ip": pi_ip,
                    "registered": True
                },
                headers={"Authorization": "Bearer change-me-in-production"}
            )
        logger.info(f"Notified PC at {device_ip} of registration with Pi at {pi_ip}")
    except Exception as notify_err:
        logger.warning(f"Failed to notify PC of registration: {notify_err}")
        # Don't fail the whole registration if notification fails
    
    return {
        "success": True,
        "data": {
            "device_id": device_id,
            "hostname": device_hostname,
            "ip_address": device_ip,
            "message": "Device registered successfully"
        }
    }

