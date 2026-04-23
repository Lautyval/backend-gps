from fastapi import FastAPI
from contextlib import asynccontextmanager

# Internal Imports
from app.utils.logger_config import logger
from app.setup.middlewares import setup_middlewares
from app.api.traccar.services import TraccarService

# Routers
from app.api.user.user_route import router as auth_router
from app.api.enterprise.enterprise_route import router as enterprise_router
from app.api.traccar.traccar_route import router as traccar_router, public_router
from app.api.enterprise_user.enterprise_user_route import router as fleet_mgmt_router
from app.api.routers.reports import router as reports_router
from app.api.share_links.share_link_router import router as share_link_router
from app.api.pois.poi_router import router as poi_router
from app.api.maintenance.maintenance_router import router as maintenance_router
from app.api.alert_rules.alert_rules_router import router as alert_rules_router
from app.api.devices.device_router import router as device_router
from app.api.geofences.geofence_router import router as geofence_router
from app.api.drivers.driver_router import router as driver_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.api.traccar.services import TraccarService, FleetBroadcaster
    
    app.state.traccar_service = TraccarService()
    app.state.broadcaster = FleetBroadcaster(app.state.traccar_service)
    
    # Start centralized poller
    await app.state.broadcaster.start()
    
    # Initialize DB (Seeding part remains in a separate call or here)
    from app.provisioning import perform_initial_setup
    from app.db.dynamic_gps_db import dispose_all_engines
    try:
        await perform_initial_setup()
        logger.info("Infraestructura de Base de Datos y Semillas inicializadas.")
    except Exception as e:
        logger.error(f"Falla crítica en inicio de base de datos: {e}")
        
    yield
    await app.state.broadcaster.stop()
    await app.state.traccar_service.close()
    await dispose_all_engines() # Close all tenant connection pools

app = FastAPI(
    title="SaaS GeoInteligencia - DigitActivo API",
    version="1.0.0",
    lifespan=lifespan
)

setup_middlewares(app)

# Include Routers
app.include_router(auth_router)
app.include_router(enterprise_router)
app.include_router(traccar_router)
app.include_router(fleet_mgmt_router)
app.include_router(reports_router)
app.include_router(public_router)
app.include_router(share_link_router)
app.include_router(poi_router)
app.include_router(maintenance_router)
app.include_router(alert_rules_router)
app.include_router(device_router)
app.include_router(geofence_router)
app.include_router(driver_router)


@app.get("/")
async def root():
    return {
        "message": "DigitActivo GPS API - Modular Backend",
        "status": "online",
        "docs": "/docs"
    }

