# ====================================================================
# SRMS — SMART RIVER MONITORING SYSTEM, VARUNA RIVER BASIN
# Centralized Digital Platform: REST API (FastAPI) serving the Next.js frontend
# ====================================================================
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.routes import app_router
from app.api.service.simulator_svc.live import run_forever
from app.conf.logging.applog import logger
from app.conf.settings import settings
from app.database.config.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    simulator = asyncio.create_task(run_forever()) if settings.SIMULATE_LIVE else None
    yield
    logger.info("Shutting down application...")
    if simulator:
        simulator.cancel()
    await engine.dispose()


app = FastAPI(
    title="SRMS — Smart River Monitoring System API",
    description="IoT stations, SMART-STREAM boat, LC-HRMS fingerprinting, TEM and drone surveys — Varuna River Basin",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_API_DOCS else None,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "ok"}


app.include_router(app_router, prefix="/api")
