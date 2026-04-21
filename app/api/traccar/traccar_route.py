from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from typing import List
from datetime import datetime, timedelta, timezone
import asyncio
import logging

from app.auth.dependencies import get_current_user
from .schema import (
    Device, DeviceCreate, DeviceUpdate,
    Geofence, GeofenceCreate,
    Driver, DriverCreate, DriverUpdate
)
from .services import TraccarService

logger = logging.getLogger("app_logger")
router = APIRouter(prefix="/fleet", tags=["Fleet"])

def get_traccar_service():
    return TraccarService()

@router.get("/status", response_model=List[Device], dependencies=[Depends(get_current_user)])
async def get_fleet_status(traccar: TraccarService = Depends(get_traccar_service)):
    return await traccar.get_devices()

@router.websocket("/stream")
async def fleet_stream(websocket: WebSocket, traccar: TraccarService = Depends(get_traccar_service)):
    await websocket.accept()
    logger.info("WS: Cliente conectado.")
    last_fetch = datetime.now(timezone.utc) - timedelta(minutes=1)
    try:
        while True:
            positions = await traccar.get_positions()
            now = datetime.now(timezone.utc)
            events = await traccar.get_events(
                from_time=(last_fetch - timedelta(minutes=2)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                to_time=now.strftime('%Y-%m-%dT%H:%M:%SZ')
            )
            last_fetch = now
            await websocket.send_json({
                "type": "update",
                "positions": [p.model_dump() for p in positions],
                "events": [e.model_dump() for e in events]
            })
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        logger.info("WS: Cliente desconectado.")

# --- Devices CRUD ---

@router.post("/devices", response_model=Device, dependencies=[Depends(get_current_user)])
async def create_device(device: DeviceCreate, traccar: TraccarService = Depends(get_traccar_service)):
    return await traccar.create_device(device)

@router.put("/devices/{id}", response_model=Device, dependencies=[Depends(get_current_user)])
async def update_device(id: int, updates: DeviceUpdate, traccar: TraccarService = Depends(get_traccar_service)):
    return await traccar.update_device(id, updates)

@router.delete("/devices/{id}", dependencies=[Depends(get_current_user)])
async def delete_device(id: int, traccar: TraccarService = Depends(get_traccar_service)):
    await traccar.delete_device(id)
    return {"status": "deleted"}

# --- Geofences CRUD ---

@router.get("/geofences", response_model=List[Geofence], dependencies=[Depends(get_current_user)])
async def get_geofences(traccar: TraccarService = Depends(get_traccar_service)):
    return await traccar.get_geofences()

@router.post("/geofences", response_model=Geofence, dependencies=[Depends(get_current_user)])
async def create_geofence(geofence: GeofenceCreate, traccar: TraccarService = Depends(get_traccar_service)):
    return await traccar.create_geofence(geofence)

@router.put("/geofences/{id}", response_model=Geofence, dependencies=[Depends(get_current_user)])
async def update_geofence(id: int, geofence: Geofence, traccar: TraccarService = Depends(get_traccar_service)):
    return await traccar.update_geofence(id, geofence)

@router.delete("/geofences/{id}", dependencies=[Depends(get_current_user)])
async def delete_geofence(id: int, traccar: TraccarService = Depends(get_traccar_service)):
    await traccar.delete_geofence(id)
    return {"status": "deleted"}

# --- Drivers CRUD ---

@router.get("/drivers", response_model=List[Driver], dependencies=[Depends(get_current_user)])
async def get_drivers(traccar: TraccarService = Depends(get_traccar_service)):
    return await traccar.get_drivers()

@router.post("/drivers", response_model=Driver, dependencies=[Depends(get_current_user)])
async def create_driver(driver: DriverCreate, traccar: TraccarService = Depends(get_traccar_service)):
    return await traccar.create_driver(driver)

@router.put("/drivers/{id}", response_model=Driver, dependencies=[Depends(get_current_user)])
async def update_driver(id: int, updates: DriverUpdate, traccar: TraccarService = Depends(get_traccar_service)):
    return await traccar.update_driver(id, updates)

@router.delete("/drivers/{id}", dependencies=[Depends(get_current_user)])
async def delete_driver(id: int, traccar: TraccarService = Depends(get_traccar_service)):
    await traccar.delete_driver(id)
    return {"status": "deleted"}

@router.post("/drivers/{driver_id}/assign/{device_id}", response_model=Driver, dependencies=[Depends(get_current_user)])
async def assign_driver(driver_id: int, device_id: int, traccar: TraccarService = Depends(get_traccar_service)):
    return await traccar.assign_driver_to_device(driver_id, device_id)
