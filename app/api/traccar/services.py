import httpx
import logging
import random
import math
from datetime import datetime, timezone, timedelta
from typing import List

from app.api.traccar.config import settings
from app.schemas import Device, Position, DeviceCreate, Geofence, GeofenceCreate, RoutePoint

logger = logging.getLogger(__name__)

class TraccarService:
    def __init__(self):
        # HTTPX AsyncClient optimizado para reutilizar la conexión TLS/TCP
        self.client = httpx.AsyncClient(
            base_url=settings.TRACCAR_URL,
            auth=(settings.TRACCAR_USERNAME, settings.TRACCAR_PASSWORD),
            timeout=5.0
        )
        
        # Setup del Fallback de Mocking (La Plata, Argentina)
        self._mock_devices = [
            {"id": 1, "name": "Unidad 1 - DigitActivo"},
            {"id": 2, "name": "Unidad 2 - DigitActivo"}
        ]
        
        # Coordenadas iniciales cerca de Plaza Moreno, La Plata
        self._mock_state = {
            1: {"lat": -34.9205, "lon": -57.9536, "speed": 40.0, "course": 90.0, "fuel": 100},
            2: {"lat": -34.9250, "lon": -57.9550, "speed": 35.0, "course": 180.0, "fuel": 85}
        }

    async def close(self):
        """Cierra de manera elegante el cliente HTTP."""
        await self.client.aclose()

    def _generate_mock_movement(self):
        """Generador heurístico de movimiento para la demo."""
        for device_id, state in self._mock_state.items():
            # Movimiento aleatorio muy ligero (~ ±50 metros)
            state["lat"] += random.uniform(-0.0002, 0.0002)
            state["lon"] += random.uniform(-0.0002, 0.0002)
            
            # Dinámica de métricas
            state["speed"] = max(0.0, min(100.0, state["speed"] + random.uniform(-8.0, 8.0)))
            state["course"] = (state["course"] + random.uniform(-15.0, 15.0)) % 360
            state["fuel"] = max(0, state["fuel"] - random.uniform(0.0, 0.2))

    async def get_devices(self) -> List[Device]:
        try:
            response = await self.client.get("/api/devices")
            response.raise_for_status()
            data = response.json()
            if data:
                return [Device(**d) for d in data]
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(f"Traccar no está disponible o devolvió un error ({e}). Activando modo MOCK.")
        
        # MOCK FALLBACK
        return [
            Device(
                id=d["id"], 
                name=d["name"], 
                status="online",
                lastUpdate="2026-01-01T00:00:00Z"
            ) for d in self._mock_devices
        ]

    async def get_positions(self) -> List[Position]:
        try:
            response = await self.client.get("/api/positions")
            response.raise_for_status()
            data = response.json()
            if data:
                return [Position(**d) for d in data]
        except (httpx.RequestError, httpx.HTTPStatusError):
            pass 
            
        # MOCK FALLBACK con actualizaciones dinámicas
        self._generate_mock_movement()
        
        return [
            Position(
                id=d["id"],
                deviceId=d["id"],
                latitude=self._mock_state[d["id"]]["lat"],
                longitude=self._mock_state[d["id"]]["lon"],
                speed=round(self._mock_state[d["id"]]["speed"], 2),
                course=round(self._mock_state[d["id"]]["course"], 2),
                attributes={
                    "fuel_level": round(self._mock_state[d["id"]]["fuel"], 1),
                    "driver_name": f"Chofer {'Carlos' if d['id'] == 1 else 'Lucia'} ({d['name']})"
                }
            ) for d in self._mock_devices
        ]

    async def create_device(self, device: DeviceCreate) -> Device:
        """Crea un nuevo dispositivo en Traccar."""
        try:
            response = await self.client.post("/api/devices", json=device.model_dump())
            response.raise_for_status()
            data = response.json()
            return Device(**data)
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Error creando dispositivo: {e}")
            raise

    async def get_geofences(self) -> List[Geofence]:
        """Obtiene las geocercas actuales."""
        try:
            response = await self.client.get("/api/geofences")
            response.raise_for_status()
            data = response.json()
            if data:
                return [Geofence(**g) for g in data]
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(f"Error obteniendo geocercas ({e}).")
        return []

    async def create_geofence(self, geofence: GeofenceCreate) -> Geofence:
        """Crea una nueva geocerca en Traccar."""
        try:
            response = await self.client.post("/api/geofences", json=geofence.model_dump())
            response.raise_for_status()
            data = response.json()
            return Geofence(**data)
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Error creando geocerca: {e}")
            raise

    async def update_geofence(self, geofence_id: int, geofence: Geofence) -> Geofence:
        """Actualiza una geocerca existente en Traccar."""
        try:
            response = await self.client.put(f"/api/geofences/{geofence_id}", json=geofence.model_dump())
            response.raise_for_status()
            data = response.json()
            return Geofence(**data)
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Error actualizando geocerca {geofence_id}: {e}")
            raise

    async def delete_geofence(self, geofence_id: int):
        """Elimina una geocerca en Traccar."""
        try:
            response = await self.client.delete(f"/api/geofences/{geofence_id}")
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Error eliminando geocerca {geofence_id}: {e}")
            raise

    async def get_route_history(self, device_id: int, from_time: str, to_time: str) -> List[RoutePoint]:
        """Obtiene el historial de posiciones de Traccar. Con fallback a un mock de ruta circular."""
        try:
            response = await self.client.get(
                "/api/positions",
                params={"deviceId": device_id, "from": from_time, "to": to_time}
            )
            response.raise_for_status()
            data = response.json()
            if data:
                return [RoutePoint(**p) for p in data]
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(f"No se pudo obtener historial de Traccar ({e}). Generando ruta MOCK.")

        # MOCK FALLBACK: genera una ruta circular realista alrededor de La Plata
        return self._generate_mock_route(device_id, from_time, to_time)

    def _generate_mock_route(self, device_id: int, from_time: str, to_time: str) -> List[RoutePoint]:
        """Genera una ruta simulada realista con ~200 puntos en un rango de tiempo."""
        try:
            dt_from = datetime.fromisoformat(from_time.replace("Z", "+00:00"))
            dt_to = datetime.fromisoformat(to_time.replace("Z", "+00:00"))
        except ValueError:
            dt_from = datetime.now(timezone.utc).replace(hour=8, minute=0, second=0)
            dt_to = dt_from + timedelta(hours=8)

        total_seconds = int((dt_to - dt_from).total_seconds())
        num_points = min(200, max(20, total_seconds // 120))  # 1 punto cada ~2 min

        # Centro de La Plata con radio de ~0.02 grados (~2km)
        center_lat = -34.9205 + (device_id * 0.005)
        center_lon = -57.9536
        radius = 0.018

        route = []
        for i in range(num_points):
            # Ruta en forma de "8" para que sea más interesante que un círculo simple
            angle = (2 * math.pi * i / num_points)
            loop = math.sin(angle * 2) * 0.4  # factor figura 8

            lat = center_lat + radius * math.sin(angle) * (1 + loop * 0.3)
            lon = center_lon + radius * math.cos(angle) * (1 - loop * 0.2)

            # Añadir algo de ruido para que parezca GPS real
            lat += random.gauss(0, 0.0001)
            lon += random.gauss(0, 0.0001)

            # Velocidad variable: más rápido en rectas, más lento en curvas
            speed_base = 25 + 15 * abs(math.cos(angle * 3))
            speed = max(0, speed_base + random.gauss(0, 5))

            # Paradas ocasionales (probab. 5%)
            if random.random() < 0.05:
                speed = 0

            course = (math.degrees(angle) + 90) % 360

            point_time = dt_from + timedelta(seconds=(total_seconds * i / num_points))

            route.append(RoutePoint(
                id=i + 1,
                deviceId=device_id,
                latitude=round(lat, 6),
                longitude=round(lon, 6),
                speed=round(speed, 1),
                course=round(course, 1),
                fixTime=point_time.isoformat(),
                serverTime=point_time.isoformat()
            ))

        return route
