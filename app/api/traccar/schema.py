from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Base Traccar Schemas ---

class Device(BaseModel):
    id: int
    name: str
    uniqueId: str
    status: str
    lastUpdate: Optional[str] = None
    disabled: bool = False
    attributes: Dict[str, Any] = {}

class DeviceCreate(BaseModel):
    name: str
    uniqueId: str
    phone: Optional[str] = None
    model: Optional[str] = None
    contact: Optional[str] = None
    category: Optional[str] = None
    disabled: bool = False

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    uniqueId: Optional[str] = None
    phone: Optional[str] = None
    model: Optional[str] = None
    contact: Optional[str] = None
    category: Optional[str] = None
    disabled: Optional[bool] = None

class Position(BaseModel):
    id: int
    deviceId: int
    protocol: Optional[str] = None
    serverTime: Optional[str] = None
    deviceTime: Optional[str] = None
    fixTime: Optional[str] = None
    outdated: bool = False
    valid: bool = True
    latitude: float
    longitude: float
    altitude: float = 0.0
    speed: float
    course: float
    address: Optional[str] = None
    accuracy: float = 0.0
    network: Optional[Dict[str, Any]] = None
    attributes: Dict[str, Any] = {}

# --- Geofence Schemas ---

class Geofence(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    area: str
    calendarId: Optional[int] = None
    attributes: Dict[str, Any] = {}

class GeofenceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    area: str
    calendarId: Optional[int] = None
    attributes: Dict[str, Any] = {}

# --- Route and Alert Schemas ---

class RoutePoint(BaseModel):
    id: int
    deviceId: int
    latitude: float
    longitude: float
    speed: float
    course: float
    fixTime: str
    serverTime: Optional[str] = None
    attributes: Dict[str, Any] = {}

class Alert(BaseModel):
    id: int
    deviceId: int
    type: str
    eventTime: str
    positionId: Optional[int] = None
    geofenceId: Optional[int] = None
    maintenanceId: Optional[int] = None
    attributes: Dict[str, Any] = {}

# --- Report Schemas ---

class ReportSummary(BaseModel):
    deviceId: int
    deviceName: str
    distance: float
    averageSpeed: float
    maxSpeed: float
    spentFuel: float
    startOdometer: float
    endOdometer: float
    startTime: str
    endTime: str
    engineHours: int = 0

class ReportTrip(BaseModel):
    deviceId: int
    deviceName: str
    distance: float
    averageSpeed: float
    maxSpeed: float
    spentFuel: float
    duration: int
    startTime: str
    endTime: str
    startLat: float
    startLon: float
    endLat: float
    endLon: float
    startAddress: Optional[str] = None
    endAddress: Optional[str] = None
    startPositionId: int
    endPositionId: int

class ReportStop(BaseModel):
    deviceId: int
    deviceName: str
    duration: int
    startTime: str
    endTime: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    distance: float = 0.0
    averageSpeed: float = 0.0
    maxSpeed: float = 0.0
    spentFuel: float = 0.0
    positionId: int

# --- Driver Schemas ---

class Driver(BaseModel):
    id: int
    name: str
    uniqueId: str
    attributes: Dict[str, Any] = {}

class DriverCreate(BaseModel):
    name: str
    uniqueId: str
    attributes: Optional[Dict[str, Any]] = None

class DriverUpdate(BaseModel):
    name: Optional[str] = None
    uniqueId: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
