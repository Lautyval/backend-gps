from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from typing import List
from datetime import datetime, timedelta, timezone
import asyncio
import logging
import os

from jose import jwt, JWTError
from app.auth.dependencies import get_current_user, get_active_enterprise
from app.api.enterprise.enterprise_model import Enterprise
from app.db.gps_db import get_async_db_session
from sqlalchemy import select, delete

from .schema import (
    Device, DeviceCreate, DeviceUpdate,
    Geofence, GeofenceCreate,
    Driver, DriverCreate, DriverUpdate,
    RoutePoint
)
from .services import TraccarService
from app.api.devices.device_model import Device as DeviceModel
from app.api.geofences.geofence_model import Geofence as GeofenceModel
from app.api.drivers.driver_model import Driver as DriverModel
from app.api.drivers import driver_repository
from app.api.devices import device_repository

logger = logging.getLogger("app_logger")
router = APIRouter(prefix="/fleet", tags=["Fleet"])

def get_traccar_service():
    return TraccarService()

@router.get("/status", response_model=List[Device])
async def get_fleet_status(
    enterprise: Enterprise = Depends(get_active_enterprise),
    traccar: TraccarService = Depends(get_traccar_service)
):
    # Fetch all devices from Traccar
    all_devices = await traccar.get_devices()
    
    # Fetch allowed traccar_device_ids from tenant DB (only enabled ones)
    async with get_async_db_session(enterprise.id) as db:
        result = await db.execute(
            select(DeviceModel.traccar_device_id)
            .where(DeviceModel.disabled == False)
        )
        allowed_ids = {row[0] for row in result.all()}

    
    # Filter
    return [d for d in all_devices if d.id in allowed_ids]

@router.get("/stream")
async def fleet_stream(
    request: Request,
    token: str = Query(None),
):
    # Auth & Enterprise detection
    from app.auth.jwt_handler import decode_access_token
    from app.api.user.user_model import User
    from app.db.main_db import AsyncSessionMain
    import json

    payload = decode_access_token(token) if token else None
    if not payload:
        raise HTTPException(status_code=401, detail="No autorizado")

    user_id = int(payload["sub"])
    async with AsyncSessionMain() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.enterprises:
            raise HTTPException(status_code=403, detail="Sin empresa asignada")
        enterprise_id = user.enterprises[0].id

    broadcaster = request.app.state.broadcaster
    queue = broadcaster.subscribe()

    async def event_generator():
        try:
            while True:
                # Si el cliente cerró la conexión, salimos
                if await request.is_disconnected():
                    break
                
                # Wait for data from broadcaster
                data = await queue.get()
                
                # Get allowed device IDs for this enterprise
                async with get_async_db_session(enterprise_id) as db:
                    res = await db.execute(select(DeviceModel.traccar_device_id))
                    allowed_ids = {row[0] for row in res.all()}

                # Filter positions and events
                data["positions"] = [p for p in data["positions"] if p["deviceId"] in allowed_ids]
                data["events"] = [e for e in data["events"] if e["deviceId"] in allowed_ids]

                yield f"data: {json.dumps(data)}\n\n"
        finally:
            broadcaster.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

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

@router.get("/geofences", response_model=List[Geofence])
async def get_geofences(
    enterprise: Enterprise = Depends(get_active_enterprise),
    traccar: TraccarService = Depends(get_traccar_service)
):
    all_geofences = await traccar.get_geofences()
    async with get_async_db_session(enterprise.id) as db:
        result = await db.execute(select(GeofenceModel.traccar_geofence_id))
        allowed_ids = {row[0] for row in result.all()}
    return [g for g in all_geofences if g.id in allowed_ids]

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

@router.get("/drivers", response_model=List[Driver])
async def get_drivers(
    enterprise: Enterprise = Depends(get_active_enterprise),
    traccar: TraccarService = Depends(get_traccar_service)
):
    all_drivers = await traccar.get_drivers()
    async with get_async_db_session(enterprise.id) as db:
        from app.api.drivers.driver_device_model import DriverDeviceLink
        
        # 1. Fetch all drivers from this tenant (including disabled ones)
        result = await db.execute(
            select(DriverModel)
        )
        db_drivers_list = result.scalars().all()
        db_drivers_map = {d.traccar_driver_id: d for d in db_drivers_list if d.traccar_driver_id}

        
        # 2. Fetch all links for these drivers
        driver_uniques = [d.unique_id for d in db_drivers_list]
        links_res = await db.execute(
            select(DriverDeviceLink).where(DriverDeviceLink.driver_unique_id.in_(driver_uniques))
        )
        links = links_res.scalars().all()
        
        # Group links by driver
        links_map = {}
        for link in links:
            if link.driver_unique_id not in links_map:
                links_map[link.driver_unique_id] = []
            links_map[link.driver_unique_id].append(link.device_unique_id)
    
    # Merge Postgres data into Traccar driver objects
    filtered_drivers = []
    for d in all_drivers:
        if d.id in db_drivers_map:
            db_driver = db_drivers_map[d.id]
            # Inject local assignment data (LIST of IDs)
            d.assigned_vehicle_ids = links_map.get(db_driver.unique_id, [])
            d.disabled = db_driver.disabled
            filtered_drivers.append(d)

            
    return filtered_drivers



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

@router.post("/drivers/{driver_unique_id}/assign/{device_unique_id}", response_model=Driver)
async def assign_driver(
    driver_unique_id: str, 
    device_unique_id: str, 
    enterprise: Enterprise = Depends(get_active_enterprise),
    traccar: TraccarService = Depends(get_traccar_service)
):
    async with get_async_db_session(enterprise.id) as db:
        # 1. Resolve Driver Unique ID to Traccar Driver ID
        db_driver = await driver_repository.get_by_unique_id(db, driver_unique_id)
        if not db_driver:
            raise HTTPException(status_code=404, detail=f"Chofer con identificador {driver_unique_id} no encontrado")
        
        traccar = TraccarService()

        # Auto-fix: if traccar_driver_id is None, register it now
        if db_driver.traccar_driver_id is None:
            try:
                from .schema import DriverCreate as TraccarDriverCreate
                new_traccar_drv = await traccar.create_driver(TraccarDriverCreate(
                    name=db_driver.name,
                    uniqueId=db_driver.unique_id
                ))
                db_driver.traccar_driver_id = new_traccar_drv.id
                await db.commit()
                await db.refresh(db_driver)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"No se pudo sincronizar chofer con Traccar: {e}")

        # 2. Resolve Device Unique ID to Traccar Device ID
        db_device = await device_repository.get_by_unique_id(db, device_unique_id)
        if not db_device:
            raise HTTPException(status_code=404, detail=f"Dispositivo con identificador {device_unique_id} no encontrado")

        # 3. Perform assignment in Traccar (optional sync)
        try:
            await traccar.assign_driver_to_device(db_driver.traccar_driver_id, db_device.traccar_device_id)
        except Exception as e:
            print(f"Warning: Traccar assignment sync failed: {e}")

        # 4. Save assignment in Postgres (Many-to-Many)
        from app.api.drivers.driver_device_model import DriverDeviceLink
        # Check if link exists
        res = await db.execute(
            select(DriverDeviceLink).where(
                DriverDeviceLink.driver_unique_id == driver_unique_id,
                DriverDeviceLink.device_unique_id == device_unique_id
            )
        )
        if not res.scalar_one_or_none():
            link = DriverDeviceLink(driver_unique_id=driver_unique_id, device_unique_id=device_unique_id)
            db.add(link)
            await db.commit()

        # 5. Return updated driver object with its links
        links_res = await db.execute(
            select(DriverDeviceLink.device_unique_id).where(DriverDeviceLink.driver_unique_id == driver_unique_id)
        )
        assigned_ids = [row[0] for row in links_res.all()]
        
        all_traccar = await traccar.get_drivers()
        traccar_drv = next((d for d in all_traccar if d.id == db_driver.traccar_driver_id), None)
        if traccar_drv:
            traccar_drv.assigned_vehicle_ids = assigned_ids
            return traccar_drv
        
        raise HTTPException(status_code=500, detail="Error al recuperar datos actualizados")



@router.delete("/drivers/{driver_unique_id}/unassign/{device_unique_id}", response_model=Driver)
async def unassign_driver(
    driver_unique_id: str,
    device_unique_id: str,
    enterprise: Enterprise = Depends(get_active_enterprise),
    traccar: TraccarService = Depends(get_traccar_service)
):
    async with get_async_db_session(enterprise.id) as db:
        from app.api.drivers.driver_device_model import DriverDeviceLink
        
        # Remove link
        await db.execute(
            delete(DriverDeviceLink).where(
                DriverDeviceLink.driver_unique_id == driver_unique_id,
                DriverDeviceLink.device_unique_id == device_unique_id
            )
        )
        await db.commit()
        
        # Get updated driver to return
        db_driver = await driver_repository.get_by_unique_id(db, driver_unique_id)
        if not db_driver:
            raise HTTPException(status_code=404, detail="Chofer no encontrado")
            
        links_res = await db.execute(
            select(DriverDeviceLink.device_unique_id).where(DriverDeviceLink.driver_unique_id == driver_unique_id)
        )
        assigned_ids = [row[0] for row in links_res.all()]
        
        all_traccar = await traccar.get_drivers()
        traccar_drv = next((d for d in all_traccar if d.id == db_driver.traccar_driver_id), None)
        if traccar_drv:
            traccar_drv.assigned_vehicle_ids = assigned_ids
            return traccar_drv
            
        raise HTTPException(status_code=500, detail="Error al recuperar datos")





# --- Route History ---

@router.get("/history/{device_id}", response_model=List[RoutePoint])
async def get_route_history(
    device_id: int, 
    from_time: str, 
    to_time: str, 
    enterprise: Enterprise = Depends(get_active_enterprise),
    traccar: TraccarService = Depends(get_traccar_service)
):
    # Verify device ownership
    async with get_async_db_session(enterprise.id) as db:
        result = await db.execute(select(DeviceModel).where(DeviceModel.traccar_device_id == device_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Acceso denegado a esta unidad.")
            
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
        enterprise_id: int = payload.get("ent")
        
        if not enterprise_id:
            raise HTTPException(status_code=403, detail="Token mal formado (sin empresa)")

    except JWTError as e:
        raise HTTPException(status_code=403, detail=f"Token expirado o inválido: {e}")

    # Check if revoked in the tenant database
    from app.api.share_links import share_links_repository as share_repo
    async with get_async_db_session(enterprise_id) as db:
        is_revoked = await share_repo.is_token_revoked(db, token)
        if is_revoked:
            raise HTTPException(status_code=403, detail="Este enlace ha sido revocado.")

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
