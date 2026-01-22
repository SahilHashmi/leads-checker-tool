from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .db.mongodb import connect_to_mongo, close_mongo_connection
from .api.routes import auth, leads, admin
from .core.config import settings
from .core.logger import app_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app_logger.info("="*60)
    app_logger.info("Starting Leads Checker Tool API")
    app_logger.info(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    app_logger.info(f"MongoDB URL: {settings.MONGODB_URL}")
    app_logger.info(f"MongoDB Database: {settings.MONGODB_DATABASE}")
    app_logger.info("="*60)
    
    try:
        await connect_to_mongo()
        app_logger.info("Application startup completed successfully")
    except Exception as e:
        app_logger.error(f"Application startup failed: {type(e).__name__}: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    app_logger.info("Shutting down application...")
    await close_mongo_connection()
    app_logger.info("Application shutdown completed")


app = FastAPI(
    title="Leads Checker Tool API",
    description="API for checking and filtering leaked email leads",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(leads.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/")
async def root():
    app_logger.debug("Root endpoint accessed")
    return {
        "name": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    app_logger.debug("Health check endpoint accessed")
    return {"status": "healthy"}
