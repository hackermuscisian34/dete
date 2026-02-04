"""
Configuration settings for APT Defender Pi Agent
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Project Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8443
    ssl_cert_path: str = Field(
        default="", 
        validation_alias="SSL_CERT"
    )
    ssl_key_path: str = Field(
        default="", 
        validation_alias="SSL_KEY"
    )
    
    # Database
    database_url: str = Field(
        default="",
        validation_alias="DATABASE_URL"
    )
    
    # JWT Configuration
    jwt_secret: str = "CHANGE_THIS_SECRET_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Security
    pairing_token_expiry_minutes: int = 15
    max_failed_auth_attempts: int = 5
    
    # Detection settings
    scan_interval_hours: int = 24
    auto_quarantine: bool = True
    alert_threshold_severity: int = 7
    
    # Network IDS
    network_ids_enabled: bool = True
    zeek_log_path: str = "/var/log/zeek"
    
    # File paths
    @property
    def final_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite+aiosqlite:///{self.base_dir}/data/defender.db"

    @property
    def final_ssl_cert(self) -> str:
        return self.ssl_cert_path or str(self.base_dir / "certs" / "server.crt")

    @property
    def final_ssl_key(self) -> str:
        return self.ssl_key_path or str(self.base_dir / "certs" / "server.key")

    quarantine_dir: str = ""
    yara_rules_dir: str = ""
    temp_dir: str = "/tmp/apt-defender"

    @property
    def final_quarantine_dir(self) -> str:
        return self.quarantine_dir or str(self.base_dir / "quarantine")

    @property
    def final_yara_rules_dir(self) -> str:
        return self.yara_rules_dir or str(self.base_dir / "yara_rules")
    
    # Cloud Sync (Supabase)
    CLOUD_SYNC_ENABLED: bool = False
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # Helper service configuration
    helper_port: int = 7890
    helper_timeout_seconds: int = 30
    helper_heartbeat_interval_seconds: int = 60

    helper_client_cert_path: str = Field(
        default="",
        validation_alias="HELPER_CLIENT_CERT"
    )
    helper_client_key_path: str = Field(
        default="",
        validation_alias="HELPER_CLIENT_KEY"
    )
    helper_ca_cert_path: str = Field(
        default="",
        validation_alias="HELPER_CA_CERT"
    )
    helper_tls_verify: bool = Field(
        default=False,
        validation_alias="HELPER_TLS_VERIFY"
    )
    

# Global settings instance
settings = Settings()
print(f"DEBUG: Settings initialized. SSL Cert Path: {settings.ssl_cert_path}")
