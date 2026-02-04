"""
Database models and initialization
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint, event
from sqlalchemy.sql import func
from config.settings import settings
from pathlib import Path
import aiosqlite

Base = declarative_base()

# ============================================
# SQLAlchemy Models
# ============================================

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String, nullable=False)
    os = Column(String, nullable=False)
    os_version = Column(String)
    paired_at = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime, server_default=func.now(), onupdate=func.now())
    status = Column(String, default='online')
    ip_address = Column(String)
    helper_version = Column(String)
    pairing_token = Column(String, unique=True)
    cert_fingerprint = Column(String)

class Threat(Base):
    __tablename__ = "threats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey('devices.id', ondelete='CASCADE'), nullable=False)
    detected_at = Column(DateTime, server_default=func.now())
    severity = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    indicator = Column(String, nullable=False)
    hash_value = Column(String)
    explanation = Column(Text, nullable=False)
    recommended_action = Column(String)
    action_taken = Column(String)
    dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime)
    dismissed_reason = Column(Text)
    evidence = Column(Text)  # JSON string

class Scan(Base):
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey('devices.id', ondelete='CASCADE'), nullable=False)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    status = Column(String, default='running')
    total_files = Column(Integer, default=0)
    files_checked = Column(Integer, default=0)
    threats_found = Column(Integer, default=0)
    scan_type = Column(String, default='full')
    error_message = Column(Text)

class NetworkEvent(Base):
    __tablename__ = "network_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey('devices.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    src_ip = Column(String, nullable=False)
    dst_ip = Column(String, nullable=False)
    src_port = Column(Integer)
    dst_port = Column(Integer)
    protocol = Column(String)
    alert_type = Column(String)
    process_name = Column(String)
    process_pid = Column(Integer)
    bytes_sent = Column(Integer, default=0)
    bytes_received = Column(Integer, default=0)

class Action(Base):
    __tablename__ = "actions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey('devices.id', ondelete='CASCADE'), nullable=False)
    threat_id = Column(Integer, ForeignKey('threats.id', ondelete='SET NULL'))
    timestamp = Column(DateTime, server_default=func.now())
    action_type = Column(String, nullable=False)
    target = Column(String, nullable=False)
    result = Column(String, default='pending')
    error_message = Column(Text)
    initiated_by = Column(String, nullable=False)
    reversible = Column(Boolean, default=True)
    reversed_at = Column(DateTime)

class ForensicTimeline(Base):
    __tablename__ = "forensic_timeline"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey('devices.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    event_type = Column(String, nullable=False)
    details = Column(Text, nullable=False)
    source = Column(String, nullable=False)
    severity = Column(Integer, default=0)

class YaraRule(Base):
    __tablename__ = "yara_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    rule_content = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    description = Column(Text)
    author = Column(String)
    author = Column(String)
    tags = Column(String)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime)
    role = Column(String, default='user')

class PairingToken(Base):
    __tablename__ = "pairing_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)
    created_by = Column(Integer, ForeignKey('users.id'))

class DeviceUser(Base):
    __tablename__ = "device_users"
    
    device_id = Column(Integer, ForeignKey('devices.id', ondelete='CASCADE'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    access_level = Column(String, default='viewer')
    granted_at = Column(DateTime, server_default=func.now())

# ============================================
# Database Engine and Session
# ============================================

engine = create_async_engine(
    settings.final_database_url,
    echo=False,  # Set to True for SQL logging
)

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        yield session

async def init_database():
    """Initialize database from schema.sql"""
    # Read schema SQL
    schema_path = Path(__file__).parent.parent.parent / "database" / "schema.sql"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Extract database path from URL
    # Handle sqlite+aiosqlite:///path (3 slashes) or sqlite+aiosqlite:////path (4 slashes)
    db_url = settings.final_database_url
    if ":////" in db_url:
        db_path = db_url.split(":////")[1]
        if not db_path.startswith("/"):
            db_path = "/" + db_path
    elif ":///" in db_url:
        db_path = db_url.split(":///")[1]
    else:
        db_path = db_url.split("://")[1]
    
    # Ensure directory exists
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Create database using aiosqlite
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(schema_sql)
        await db.commit()
    
    print(f"✅ Database initialized: {db_path}")
