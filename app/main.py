from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
import asyncio
import logging

from app.schemas import Device, Position, DeviceCreate, Geofence, GeofenceCreate, RoutePoint
from app.api.traccar.services import TraccarService

logging.basicConfig(level=logging.INFO)

# Instancia global del servicio
traccar_service: TraccarService

@asynccontextmanager
async def lifespan(app: FastAPI):
    global traccar_service
    traccar_service = TraccarService()
    yield # Aquí la SPA recibe peticiones
    await traccar_service.close()

app = FastAPI(
    title="Wrapper GeoInteligencia - DigitActivo API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS relajado para simplificar la Demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/fleet/status", response_model=List[Device], tags=["Fleet"])
async def get_fleet_status():
    """Devuelve un resumen de todos los vehículos activos."""
    return await traccar_service.get_devices()


@app.get("/fleet/positions", response_model=List[Position], tags=["Fleet"])
async def get_fleet_positions():
    """Devuelve las coordenadas y sensores actuales listas para el mapa."""
    return await traccar_service.get_positions()


@app.websocket("/fleet/stream")
async def fleet_stream(websocket: WebSocket):
    """WebSocket que actualiza la UI con posiciones cada 2 segundos sin re-renderizar todo."""
    await websocket.accept()
    logging.info("Frontend conectado al Streamer en Tiempo Real (WS).")
    try:
        while True:
            # Consumimos del servicio de Traccar (o del Mocker)
            positions = await traccar_service.get_positions()
            
            # Formateamos enviando Data purificada dict-like al Frontend
            await websocket.send_json([p.model_dump() for p in positions])
            
            # Polling Rate estricto
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        logging.info("Frontend desconectado del WebSocket.")

@app.post("/fleet/devices", response_model=Device, tags=["Fleet"])
async def create_fleet_device(device: DeviceCreate):
    """Crea un nuevo dispositivo en el servidor de Traccar."""
    return await traccar_service.create_device(device)

@app.get("/fleet/geofences", response_model=List[Geofence], tags=["Fleet"])
async def get_fleet_geofences():
    """Obtiene las geocercas actuales de Traccar."""
    return await traccar_service.get_geofences()

@app.post("/fleet/geofences", response_model=Geofence, tags=["Fleet"])
async def create_fleet_geofence(geofence: GeofenceCreate):
    """Crea una nueva geocerca en el servidor de Traccar."""
    return await traccar_service.create_geofence(geofence)

@app.put("/fleet/geofences/{geofence_id}", response_model=Geofence, tags=["Fleet"])
async def update_fleet_geofence(geofence_id: int, geofence: Geofence):
    """Actualiza una geocerca existente en el servidor de Traccar."""
    return await traccar_service.update_geofence(geofence_id, geofence)

@app.delete("/fleet/geofences/{geofence_id}", tags=["Fleet"])
async def delete_fleet_geofence(geofence_id: int):
    """Elimina una geocerca en el servidor de Traccar."""
    await traccar_service.delete_geofence(geofence_id)
    return {"status": "deleted"}

@app.get("/fleet/history/{device_id}", response_model=List[RoutePoint], tags=["Fleet"])
async def get_device_history(
    device_id: int,
    from_time: str,  # ISO8601 e.g. "2026-04-15T00:00:00Z"
    to_time: str     # ISO8601 e.g. "2026-04-15T23:59:59Z"
):
    """Devuelve el historial de posiciones de un dispositivo en un rango de tiempo."""
    return await traccar_service.get_route_history(device_id, from_time, to_time)
