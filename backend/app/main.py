"""Main FastAPI application"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db, close_db
from app.logging_config import setup_logging, get_logger
from app.api import webhooks, incidents, metrics, events, rules, auth, easyconnect, onboarding, detections, routing_rules, webhooks_management, analytics

# Setup logging first
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("application_starting", version=settings.APP_VERSION)
    await init_db()
    logger.info("database_initialized")
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")
    await close_db()
    logger.info("database_connections_closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade blockchain monitoring and alerting platform for Qubic",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(webhooks.router)
app.include_router(incidents.router)
app.include_router(metrics.router)
app.include_router(events.router)
app.include_router(rules.router)
app.include_router(easyconnect.router)
app.include_router(onboarding.router)
app.include_router(detections.router)
app.include_router(routing_rules.router)
app.include_router(routing_rules.logs_router)
app.include_router(webhooks_management.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health")
async def health_check():
    """Application health check"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
