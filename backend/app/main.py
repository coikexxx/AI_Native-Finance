"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.db import init_db
from app.api.routes.analysis import router as analysis_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.watchlist import router as watchlist_router
from app.api.routes.monitor import router as monitor_router

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("Starting AI Finance Research Agent...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Start alert scheduler
    from app.alerts.scheduler import alert_scheduler
    alert_scheduler.start()
    logger.info("Alert scheduler started")

    yield

    # Shutdown
    from app.alerts.scheduler import alert_scheduler
    alert_scheduler.stop()
    logger.info("Shutting down...")


app = FastAPI(
    title="AI Finance Research Agent",
    description="AI-native stock analysis platform with 9 specialist agents",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(analysis_router)
app.include_router(alerts_router)
app.include_router(watchlist_router)
app.include_router(monitor_router)


@app.get("/")
async def root():
    return {
        "service": "AI Finance Research Agent",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
