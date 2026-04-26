import httpx
import logging
import random
import math
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from app.api.traccar.config import settings
from .schema import (
    Device, Position, DeviceCreate, DeviceUpdate, Geofence, GeofenceCreate, 
    RoutePoint, Alert, ReportSummary, ReportTrip, ReportStop,
    Driver, DriverCreate, DriverUpdate
)

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
            {"id": 1, "name": "Unidad 1 - DigitActivo", "disabled": False},
            {"id": 2, "name": "Unidad 2 - DigitActivo", "disabled": False}
        ]
        self._mock_drivers = [
            {"id": 1, "name": "Carlos Gomez", "uniqueId": "DRV001", "disabled": False},
            {"id": 2, "name": "Lucia Sanchez", "uniqueId": "DRV002", "disabled": False}
        ]
        
        # Coordenadas iniciales cerca de Plaza Moreno, La Plata
        self._mock_state = {
            1: {"lat": -34.9205, "lon": -57.9536, "speed": 40.0, "course": 90.0, "fuel": 100},
            2: {"lat": -34.9250, "lon": -57.9550, "speed": 35.0, "course": 180.0, "fuel": 85}
        }
        self._mock_alert_id_counter = 100
        self._mock_driver_id_counter = len(self._mock_drivers) + 1

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
            if isinstance(data, list):
                return [Device(**d) for d in data]
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(f"Traccar no está disponible o devolvió un error ({e}). Activando modo MOCK.")
        
        # MOCK FALLBACK
        return [
            Device(
                id=d["id"], 
                name=d["name"], 
                status="online",
                lastUpdate="2026-01-01T00:00:00Z",
                disabled=d.get("disabled", False)
            ) for d in self._mock_devices
        ]

    async def get_positions(self) -> List[Position]:
        try:
            response = await self.client.get("/api/positions")
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
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
                disabled=d.get("disabled", False),
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

    async def update_device(self, device_id: int, updates: DeviceUpdate) -> Device:
        """Actualiza un dispositivo existente en Traccar (soporta actualizaciones parciales)."""
        try:
            # 1. Obtener datos actuales
            current_devices = await self.get_devices()
            current = next((d for d in current_devices if d.id == device_id), None)
            if not current:
                 raise ValueError(f"Dispositivo {device_id} no encontrado")
            
            # 2. Fusionar actualizaciones
            updated_data = current.model_dump()
            updates_dict = updates.model_dump(exclude_unset=True)
            updated_data.update(updates_dict)
            full_device = Device(**updated_data)
            full_device.id = device_id # Asegurar consistencia

            # 3. Enviar a Traccar
            response = await self.client.put(f"/api/devices/{device_id}", json=full_device.model_dump())
            response.raise_for_status()
            data = response.json()
            return Device(**data)
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            logger.error(f"Error actualizando dispositivo {device_id}: {e}")
            # Mock update
            for i, d in enumerate(self._mock_devices):
                if d["id"] == device_id:
                    # En mock, cargamos el actual y mergeamos
                    current_mock = self._mock_devices[i]
                    updates_dict = updates.model_dump(exclude_unset=True)
                    current_mock.update(updates_dict)
                    self._mock_devices[i] = current_mock
                    return Device(**current_mock)
            raise

    async def delete_device(self, device_id: int):
        """Elimina un dispositivo de Traccar."""
        try:
            response = await self.client.delete(f"/api/devices/{device_id}")
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Error eliminando dispositivo {device_id}: {e}")
            # Mock delete
            self._mock_devices = [d for d in self._mock_devices if d["id"] != device_id]
            if device_id in self._mock_state:
                del self._mock_state[device_id]

    async def get_geofences(self) -> List[Geofence]:
        """Obtiene las geocercas actuales."""
        try:
            response = await self.client.get("/api/geofences")
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
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
            if isinstance(data, list):
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

    async def get_events(self, from_time: str, to_time: str) -> List[Alert]:
        """Obtiene alertas de Traccar."""
        try:
            response = await self.client.get(
                "/api/reports/events",
                params={"from": from_time, "to": to_time, "allDevices": "true"},
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                if data:
                    logger.info(f"Traccar detectó {len(data)} eventos nuevos.")
                return [Alert(**e) for e in data]
            return []
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(f"Error obteniendo eventos de Traccar: {e}")
            return []

    async def get_report_summary(self, from_time: str, to_time: str, device_ids: List[int]) -> List[ReportSummary]:
        try:
            params = [("from", from_time), ("to", to_time)]
            for did in device_ids:
                params.append(("deviceId", str(did)))
            response = await self.client.get("/api/reports/summary", params=params, headers={"Accept": "application/json"})
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                # Calcular velocidad y distancia desde posiciones reales para sortear bug de Traccar (Vel. = 0.0)
                import math
                for e in data:
                    did = e.get("deviceId")
                    pos_resp = await self.client.get("/api/positions", params={"deviceId": did, "from": from_time, "to": to_time})
                    if pos_resp.status_code == 200:
                        positions = pos_resp.json()
                        if isinstance(positions, list) and len(positions) > 1:
                            dist = 0.0
                            total_speed = 0.0
                            for i, p in enumerate(positions):
                                total_speed += p.get("speed", 0.0)
                                if i > 0:
                                    prev = positions[i-1]
                                    dLat = (p["latitude"] - prev["latitude"]) * (math.pi / 180.0)
                                    dLon = (p["longitude"] - prev["longitude"]) * (math.pi / 180.0)
                                    a = math.sin(dLat / 2)**2 + math.cos(prev["latitude"] * (math.pi / 180.0)) * math.cos(p["latitude"] * (math.pi / 180.0)) * math.sin(dLon / 2)**2
                                    dist += 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                            
                            e["distance"] = dist * 1000.0 # m
                            e["averageSpeed"] = total_speed / len(positions)
                            
                return [ReportSummary(**e) for e in data]
        except Exception as e:
            logger.warning(f"No se pudo obtener resumen de Traccar ({e}). Generando MOCK.")
        
        # Fallback Mock
        return self._generate_mock_summary(device_ids)

    def _generate_mock_summary(self, device_ids: List[int]) -> List[ReportSummary]:
        summaries = []
        for did in device_ids:
            device_name = next((d["name"] for d in self._mock_devices if d["id"] == did), f"Unidad {did}")
            summaries.append(ReportSummary(
                deviceId=did,
                deviceName=device_name,
                distance=5900.0,
                averageSpeed=1.78,
                maxSpeed=19.16,
                spentFuel=0,
                startOdometer=15200.0,
                endOdometer=15205.9,
                startTime=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
                endTime=datetime.now(timezone.utc).isoformat(),
                engineHours=1800000 
            ))
        return summaries

    async def get_report_trips(self, from_time: str, to_time: str, device_ids: List[int]) -> List[ReportTrip]:
        try:
            params = [("from", from_time), ("to", to_time)]
            for did in device_ids:
                params.append(("deviceId", str(did)))
            response = await self.client.get("/api/reports/trips", params=params, headers={"Accept": "application/json"})
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return [ReportTrip(**e) for e in data]
        except Exception as e:
            logger.warning(f"No se pudo obtener viajes de Traccar ({e}). Generando MOCK.")
        
        return self._generate_mock_trips(device_ids, from_time, to_time)

    def _generate_mock_trips(self, device_ids: List[int], from_time: str, to_time: str) -> List[ReportTrip]:
        trips = []
        for did in device_ids:
            device_name = next((d["name"] for d in self._mock_devices if d["id"] == did), f"Unidad {did}")
            trips.append(ReportTrip(
                deviceId=did,
                deviceName=device_name,
                distance=5900.0,
                averageSpeed=1.78,
                maxSpeed=19.16,
                spentFuel=0,
                startOdometer=15200.0,
                endOdometer=15205.9,
                duration=10800000, 
                startTime=from_time,
                endTime=to_time,
                startPositionId=1001,
                endPositionId=1200,
                startLat=-34.9205,
                startLon=-57.9536,
                endLat=-34.9150,
                endLon=-57.9400,
                startAddress="Calle 7, La Plata",
                endAddress="Plaza Moreno, La Plata"
            ))
        return trips

    async def get_report_stops(self, from_time: str, to_time: str, device_ids: List[int]) -> List[ReportStop]:
        try:
            params = [("from", from_time), ("to", to_time)]
            for did in device_ids:
                params.append(("deviceId", str(did)))
            response = await self.client.get("/api/reports/stops", params=params, headers={"Accept": "application/json"})
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return [ReportStop(**e) for e in data]
        except Exception as e:
            logger.warning(f"No se pudo obtener paradas de Traccar ({e}). Generando MOCK.")
        
        return self._generate_mock_stops(device_ids, from_time, to_time)

    def _generate_mock_stops(self, device_ids: List[int], from_time: str, to_time: str) -> List[ReportStop]:
        stops = []
        for did in device_ids:
            device_name = next((d["name"] for d in self._mock_devices if d["id"] == did), f"Unidad {did}")
            stops.append(ReportStop(
                deviceId=did,
                deviceName=device_name,
                distance=0,
                averageSpeed=0,
                maxSpeed=0,
                spentFuel=0,
                startOdometer=15205.9,
                endOdometer=15205.9,
                duration=900000, 
                startTime=from_time,
                endTime=to_time,
                positionId=1201,
                address="Av. 13 e/ 50 y 51, La Plata",
                latitude=-34.9205,
                longitude=-57.9536
            ))
        return stops

    def _generate_mock_alerts(self) -> List[Alert]:
        """Genera alertas aleatorias para la demo."""
        alerts = []
        # 10% de probabilidad de generar una alerta en cada poll
        if random.random() < 0.15:
            device = random.choice(self._mock_devices)
            alert_types = [
                ("overspeed", {"speed": 115, "speedLimit": 100}, "Exceso de velocidad: 115 km/h"),
                ("geofenceEnter", {"geofenceId": 1}, "Entrada a Geocerca: Zona Norte"),
                ("geofenceExit", {"geofenceId": 2}, "Salida de Geocerca: Deposito Central"),
                ("alarm", {"alarm": "sos"}, "¡Alerta SOS recibida!"),
                ("deviceMoving", {}, "La unidad ha comenzado a moverse")
            ]
            atype, attrs, desc = random.choice(alert_types)
            self._mock_alert_id_counter += 1
            
            alerts.append(Alert(
                id=self._mock_alert_id_counter,
                deviceId=device["id"],
                type=atype,
                eventTime=datetime.now(timezone.utc).isoformat(),
                attributes={**attrs, "description": desc}
            ))
        return alerts

    async def get_drivers(self) -> List[Driver]:
        """Obtiene la lista de choferes."""
        try:
            response = await self.client.get("/api/drivers")
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return [Driver(**d) for d in data]
        except (httpx.RequestError, httpx.HTTPStatusError):
            logger.warning("Traccar no disponible para choferes. Usando MOCK.")
        
        return [Driver(**d) for d in self._mock_drivers]

    async def create_driver(self, driver: DriverCreate) -> Driver:
        """Crea un nuevo chofer."""
        try:
            response = await self.client.post("/api/drivers", json=driver.model_dump())
            response.raise_for_status()
            data = response.json()
            return Driver(**data)
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Error creando chofer: {e}. Fallback a local.")
            # Fallback mock for local testing
            new_id = self._mock_driver_id_counter
            self._mock_driver_id_counter += 1
            new_driver = Driver(id=new_id, **driver.model_dump())
            self._mock_drivers.append(new_driver.model_dump())
            return new_driver

    async def update_driver(self, driver_id: int, updates: DriverUpdate) -> Driver:
        """Actualiza un chofer (soporta actualizaciones parciales)."""
        try:
            # 1. Obtener datos actuales
            current_drivers = await self.get_drivers()
            current = next((d for d in current_drivers if d.id == driver_id), None)
            if not current:
                raise ValueError(f"Chofer {driver_id} no encontrado")

            # 2. Fusionar
            updated_data = current.model_dump()
            updates_dict = updates.model_dump(exclude_unset=True)
            updated_data.update(updates_dict)
            full_driver = Driver(**updated_data)
            full_driver.id = driver_id

            # 3. Enviar a Traccar (excluyendo campos locales que Traccar no soporta)
            payload = full_driver.model_dump()
            payload.pop("assigned_vehicle_ids", None)
            payload.pop("disabled", None)
            
            response = await self.client.put(f"/api/drivers/{driver_id}", json=payload)

            response.raise_for_status()
            data = response.json()
            return Driver(**data)
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            logger.error(f"Error actualizando chofer {driver_id}: {e}")
            # Mock update
            for i, d in enumerate(self._mock_drivers):
                if d["id"] == driver_id:
                    current_mock = self._mock_drivers[i]
                    updates_dict = updates.model_dump(exclude_unset=True)
                    current_mock.update(updates_dict)
                    self._mock_drivers[i] = current_mock
                    return Driver(**current_mock)
            raise

    async def delete_driver(self, driver_id: int):
        """Elimina un chofer."""
        try:
            response = await self.client.delete(f"/api/drivers/{driver_id}")
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Error eliminando chofer {driver_id}: {e}")
            # Mock delete
            self._mock_drivers = [d for d in self._mock_drivers if d["id"] != driver_id]

    async def assign_driver_to_device(self, driver_id: int, device_id: int) -> Driver:
        """Vincula un chofer a un dispositivo via attributes."""
        try:
            # En lugar de buscar todos los drivers, intentamos actualizar directamente
            # Si estamos en modo real, necesitamos los atributos actuales para no pisarlos.
            # Pero como nuestra arquitectura usa TraccarDriverUpdate que fusiona, podemos ser más directos.
            
            # Para mayor seguridad en Traccar real, primero obtenemos el driver por ID
            try:
                response = await self.client.get(f"/api/drivers/{driver_id}")
                if response.status_code == 200:
                    driver_data = response.json()
                    attrs = driver_data.get("attributes", {})
                    attrs["assignedDeviceId"] = device_id
                    driver_data["attributes"] = attrs
                    
                    # Update back
                    update_resp = await self.client.put(f"/api/drivers/{driver_id}", json=driver_data)
                    update_resp.raise_for_status()
                    return Driver(**update_resp.json())
            except Exception:
                # Si falla (ej: estamos en MOCK), intentamos el flujo local
                pass

            # Mock persistence fallback
            for d in self._mock_drivers:
                if d["id"] == driver_id:
                    if "attributes" not in d: d["attributes"] = {}
                    d["attributes"]["assignedDeviceId"] = device_id
                    return Driver(**d)
            
            # Si no está en mocks tampoco, lanzamos error descriptivo
            raise ValueError(f"Conductor con ID {driver_id} no encontrado en Traccar ni en Mocks")
        except Exception as e:
            logger.error(f"Error vinculando chofer {driver_id} a dispositivo {device_id}: {e}")
            raise


class FleetBroadcaster:
    def __init__(self, traccar_service: TraccarService):
        self.traccar = traccar_service
        self.subscribers: List[asyncio.Queue] = []
        self._running = False
        self._task = None

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("FleetBroadcaster iniciado")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("FleetBroadcaster detenido")

    async def _run(self):
        last_fetch = datetime.now(timezone.utc) - timedelta(minutes=1)
        while self._running:
            try:
                positions = await self.traccar.get_positions()
                now = datetime.now(timezone.utc)
                events = await self.traccar.get_events(
                    from_time=(last_fetch - timedelta(minutes=2)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    to_time=now.strftime('%Y-%m-%dT%H:%M:%SZ')
                )
                last_fetch = now
                
                payload = {
                    "type": "update",
                    "positions": [p.model_dump() for p in positions],
                    "events": [e.model_dump() for e in events]
                }
                
                # Broadcast to all queues
                for queue in self.subscribers[:]:
                    try:
                        # Si la cola está llena, removemos el item más viejo para no bloquear el broadcast
                        if queue.full():
                            queue.get_nowait()
                        await queue.put(payload)
                    except Exception:
                        pass
                
            except Exception as e:
                logger.error(f"Error en FleetBroadcaster: {e}")
            
            await asyncio.sleep(2.0)

    def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue(maxsize=10)
        self.subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self.subscribers:
            self.subscribers.remove(queue)
