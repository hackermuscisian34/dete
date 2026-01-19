"""
Pi Agent - Main entry point for APT Defender Detection Agent
"""
import sys
import os
import uvicorn
import asyncio
from pathlib import Path
from fastapi import FastAPI
from api.routes import devices, threats, actions, system
from api import auth
from database.db import init_database
from config.settings import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("agent.log")
    ]
)
logger = logging.getLogger("main")

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="APT Defender Pi Agent",
        description="Detection and response agent for Raspberry Pi",
        version="2.0.0"
    )
    
    # Include API routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
    app.include_router(threats.router, prefix="/api/v1/threats", tags=["threats"])
    app.include_router(actions.router, prefix="/api/v1/actions", tags=["actions"])
    app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
    
    @app.get("/")
    async def root():
        return {
            "name": "APT Defender Pi Agent",
            "version": "2.0.0",
            "status": "active"
        }
        
    return app

def ensure_system_ready():
    """Ensure directories and certificates exist"""
    # 1. Ensure directories exist
    dirs = [
        settings.base_dir / "data",
        settings.base_dir / "certs",
        settings.base_dir / "quarantine",
        settings.base_dir / "logs"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"DEBUG: Ensured directory exists: {d}")

    # 2. Check/Generate SSL Certificates
    cert_path = Path(settings.final_ssl_cert)
    key_path = Path(settings.final_ssl_key)
    
    if not cert_path.exists() or not key_path.exists():
        print("WARNING: SSL certificates missing. Generating self-signed certificates...")
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import datetime

            # Generate key
            key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )

            # Generate cert
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"CA"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, u"San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"APT Defender"),
                x509.NameAttribute(NameOID.COMMON_NAME, u"pi-agent"),
            ])
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                # Our certificate will be valid for 10 years
                datetime.datetime.utcnow() + datetime.timedelta(days=3650)
            ).add_extension(
                x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
                critical=False,
            ).sign(key, hashes.SHA256())

            # Write key
            with open(key_path, "wb") as f:
                f.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                ))

            # Write cert
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            print(f"✅ Generated new self-signed certificates at {cert_path}")
        except Exception as e:
            print(f"ERROR: Failed to generate certificates: {e}")
            print("Please ensure 'cryptography' is installed: pip install cryptography")

def main():
    """Main execution point"""
    try:
        # Pre-flight checks
        ensure_system_ready()
        
        # Initialize database
        print("DEBUG: Initializing database...")
        asyncio.run(init_database())
        
        # Run schema migration for new columns (V2)
        print("DEBUG: Checking for database migrations...")
        try:
            from scripts.migrate_db import migrate
            migrate()
        except ImportError:
            print("WARNING: Migration script not found.")
        except Exception as e:
            print(f"ERROR during migration: {e}")
            
        print("DEBUG: Database ready.")
        
        # Create FastAPI app
        app = create_app()
        
        # Run server
        # In development, we use HTTP if certificates are tricky, 
        # but for production mTLS is required.
        print(f"DEBUG: Starting Pi Agent on {settings.host}:{settings.port}")
        uvicorn.run(
            app, 
            host=settings.host, 
            port=settings.port,
            # We run the agent itself on HTTP for now as the mobile app might not have certs,
            # but communication TO the helper is HTTPS/mTLS.
            # ssl_keyfile=settings.final_ssl_key,
            # ssl_certfile=settings.final_ssl_cert
        )
    except Exception as e:
        logger.critical(f"Agent failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
