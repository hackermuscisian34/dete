"""
FastAPI application server
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.auth import router as auth_router
from api.routes.devices import router as devices_router
from api.routes.threats import router as threats_router
from api.routes.actions import router as actions_router
from api.routes.system import router as system_router
import logging

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="APT Defender Pi Agent API",
        description="Portable APT Detection & Response System",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # CORS middleware (restrict in production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict to mobile app origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(exc),
                    "user_message": "An unexpected error occurred. Please try again."
                }
            }
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "version": "1.0.0"
            }
        }
    
    # Include routers
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(devices_router, prefix="/api/v1/devices", tags=["Devices"])
    app.include_router(threats_router, prefix="/api/v1/threats", tags=["Threats"])
    app.include_router(actions_router, prefix="/api/v1/actions", tags=["Actions"])
    app.include_router(system_router, prefix="/api/v1/system", tags=["System"])
    
    @app.on_event("startup")
    async def startup_event():
        """Run on application startup"""
        logger.info("APT Defender API Server starting...")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Run on application shutdown"""
        logger.info("APT Defender API Server shutting down...")
    
    return app
