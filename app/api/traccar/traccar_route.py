from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from typing import List
from datetime import datetime, timedelta, timezone
import asyncio
import logging
import os

from jose import jwt, JWTError
from app.auth.dependencies import get_current_user
from .schema import (
    Device, DeviceCreate, DeviceUpdate,
    Geofence, GeofenceCreate,
    Driver, DriverCreate, DriverUpdate,
    RoutePoint
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

# --- Route History ---

@router.get("/history/{device_id}", response_model=List[RoutePoint], dependencies=[Depends(get_current_user)])
async def get_route_history(device_id: int, from_time: str, to_time: str, traccar: TraccarService = Depends(get_traccar_service)):
    return await traccar.get_route_history(device_id, from_time, to_time)

# --- Corridor Geofence ---

from pydantic import BaseModel as PydanticBase
import math

class CorridorPoint(PydanticBase):
    lat: float
    lng: float

class CorridorRequest(PydanticBase):
    name: str
    points: List[CorridorPoint]
    width_meters: float = 100.0

def _buffer_line_to_wkt(points: List[CorridorPoint], width_m: float) -> str:
    """Compute a simple rectangular buffer polygon around a polyline."""
    if len(points) < 2:
        raise ValueError("Se necesitan al menos 2 puntos para crear un corredor")

    R = 6371000.0  # Earth radius in metres
    half = width_m / 2.0

    left_side: List[tuple] = []
    right_side: List[tuple] = []

    for i, pt in enumerate(points):
        lat_rad = math.radians(pt.lat)
        # Compute bearing of the segment at this vertex
        if i < len(points) - 1:
            nxt = points[i + 1]
        else:
            nxt = points[i - 1]
        dlat = math.radians(nxt.lat - pt.lat)
        dlng = math.radians(nxt.lng - pt.lng) * math.cos(lat_rad)
        bearing = math.atan2(dlng, dlat)

        # Perpendicular offset in degrees
        perp = bearing + math.pi / 2
        dlat_deg = math.degrees(half / R)
        dlng_deg = math.degrees(half / R / math.cos(lat_rad))

        left_side.append((pt.lat + dlat_deg * math.sin(perp - math.pi / 2 + math.pi / 2),
                          pt.lng + dlng_deg * math.cos(perp - math.pi / 2 + math.pi / 2)))
        right_side.append((pt.lat - dlat_deg * math.sin(perp - math.pi / 2 + math.pi / 2),
                           pt.lng - dlng_deg * math.cos(perp - math.pi / 2 + math.pi / 2)))

    # Build polygon: left forward + right backward + close
    polygon_pts = left_side + list(reversed(right_side)) + [left_side[0]]
    # Traccar non-standard WKT: POLYGON ((lat lng, ...))
    coords_str = ", ".join(f"{lat} {lng}" for lat, lng in polygon_pts)
    return f"POLYGON (({coords_str}))"

@router.post("/corridor", dependencies=[Depends(get_current_user)])
async def create_corridor(req: CorridorRequest, traccar: TraccarService = Depends(get_traccar_service)):
    if len(req.points) < 2:
        raise HTTPException(status_code=400, detail="Se necesitan al menos 2 puntos")
    wkt = _buffer_line_to_wkt(req.points, req.width_meters)
    from .schema import GeofenceCreate
    geofence = await traccar.create_geofence(GeofenceCreate(
        name=req.name,
        description=f"Corredor de {req.width_meters:.0f}m de ancho",
        area=wkt,
        attributes={"zoneType": "corridor", "alertType": "exit"}
    ))
    return geofence

# ── Public track endpoint (no auth) ──────────────────────────────────────────
_JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
_ALGO = "HS256"

public_router = APIRouter(prefix="/track", tags=["Public Tracking"])

@public_router.get("/{token}")
async def public_track(token: str, traccar: TraccarService = Depends(get_traccar_service)):
    try:
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_ALGO])
        if payload.get("type") != "share":
            raise HTTPException(status_code=403, detail="Token inválido")
        device_id: int = payload["device_id"]
    except JWTError as e:
        raise HTTPException(status_code=403, detail=f"Token expirado o inválido: {e}")

    # Fetch all positions and find the one for this device
    positions = await traccar.get_positions()
    position = next((p for p in positions if p.deviceId == device_id), None)

    devices = await traccar.get_devices()
    device = next((d for d in devices if d.id == device_id), None)

    if position is None:
        raise HTTPException(status_code=404, detail="Posición no disponible para esta unidad")

    return {
        "device_id": device_id,
        "name": device.name if device else f"Unidad {device_id}",
        "latitude": position.latitude,
        "longitude": position.longitude,
        "speed": position.speed,
        "course": position.course,
        "last_update": position.serverTime or datetime.now(timezone.utc).isoformat(),
    }
