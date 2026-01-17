"""
Configuration settings for APT Defender Pi Agent
"""
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8443
    ssl_certfile: str = "/opt/apt-defender/certs/server.crt"
    ssl_keyfile: str = "/opt/apt-defender/certs/server.key"
    
    # Database
    database_url: str = "sqlite+aiosqlite:////opt/apt-defender/data/defender.db"
    
    # JWT Configuration
    jwt_secret: str = "CHANGE_THIS_SECRET_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Security
    pairing_token_expiry_minutes: int = 5
    max_failed_auth_attempts: int = 5
    
    # Detection settings
    scan_interval_hours: int = 24
    auto_quarantine: bool = True
    alert_threshold_severity: int = 7
    
    # Network IDS
    network_ids_enabled: bool = True
    zeek_log_path: str = "/var/log/zeek"
    
    # File paths
    quarantine_dir: str = "/opt/apt-defender/quarantine"
    yara_rules_dir: str = "/opt/apt-defender/yara_rules"
    temp_dir: str = "/tmp/apt-defender"
    
    # Cloud Sync (Supabase)
    CLOUD_SYNC_ENABLED: bool = False
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # Helper service configuration
    helper_port: int = 7890
    helper_timeout_seconds: int = 30
    helper_heartbeat_interval_seconds: int = 60
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()
