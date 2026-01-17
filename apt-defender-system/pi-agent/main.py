"""
APT Defender - Raspberry Pi Detection Agent
Main entry point
"""
import asyncio
import logging
from pathlib import Path
import uvicorn
from api.server import create_app
from database.db import init_database
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/apt-defender/agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def startup():
    """Initialize application components"""
    logger.info("=" * 60)
    logger.info("APT Defender Pi Agent Starting")
    logger.info("=" * 60)
    
    # Initialize database
    logger.info("Initializing database...")
    await init_database()
    
    # Load YARA rules
    logger.info("Loading YARA rules...")
    # TODO: Load YARA rules from config/yara_rules/
    
    # Start background tasks
    logger.info("Starting background services...")
    # TODO: Start scan scheduler, network monitor, etc.
    
    logger.info("✅ APT Defender Ready")
    logger.info(f"API listening on https://{settings.host}:{settings.port}")

def main():
    """Main application entry point"""
    try:
        # Create FastAPI app
        app = create_app()
        
        # Run server
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            ssl_keyfile=settings.ssl_keyfile,
            ssl_certfile=settings.ssl_certfile,
            log_level="info",
            on_startup=[startup] # Ensure startup function is called
        )
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


