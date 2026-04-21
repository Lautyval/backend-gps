from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

# Internal Imports
from app.logger_config import logger
from app.setup.middlewares import setup_middlewares
from app.api.traccar.services import TraccarService

# Routers
from app.api.user.user_route import router as auth_router
from app.api.enterprise.enterprise_route import router as enterprise_router
from app.api.traccar.traccar_route import router as traccar_router
from app.api.enterprise_user.enterprise_user_route import router as fleet_mgmt_router
from app.api.routers.reports import router as reports_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.traccar_service = TraccarService()
    # Initialize DB (Seeding part remains in a separate call or here)
    from app.provisioning import perform_initial_setup
    from app.db.dynamic_gps_db import dispose_all_engines
    try:
        await perform_initial_setup()
        logger.info("Infraestructura de Base de Datos y Semillas inicializadas.")
    except Exception as e:
        logger.error(f"Falla crítica en inicio de base de datos: {e}")
        
    yield
    await app.state.traccar_service.close()
    await dispose_all_engines() # Close all tenant connection pools

app = FastAPI(
    title="SaaS GeoInteligencia - DigitActivo API",
    version="3.0.0",
    lifespan=lifespan
)

setup_middlewares(app)

# Include Routers
app.include_router(auth_router)
app.include_router(enterprise_router)
app.include_router(traccar_router)
app.include_router(fleet_mgmt_router)
app.include_router(reports_router)

@app.get("/")
async def root():
    return {
        "message": "DigitActivo GPS API - Modular Backend",
        "status": "online",
        "docs": "/docs"
    }

