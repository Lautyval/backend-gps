from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional

class Device(BaseModel):
    id: int
    name: str
    uniqueId: Optional[str] = None
    status: Optional[str] = "offline"
    lastUpdate: Optional[str] = None
    
    model_config = ConfigDict(extra="ignore")

class DeviceCreate(BaseModel):
    name: str
    uniqueId: str
    model_config = ConfigDict(extra="ignore")

class Position(BaseModel):
    id: int
    deviceId: int
    latitude: float
    longitude: float
    speed: float
    course: float
    serverTime: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    model_config = ConfigDict(extra="ignore")

class Geofence(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    area: str
    model_config = ConfigDict(extra="ignore")

class GeofenceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    area: str
    model_config = ConfigDict(extra="ignore")

class RoutePoint(BaseModel):
    id: int
    deviceId: int
    latitude: float
    longitude: float
    speed: float
    course: float
    fixTime: Optional[str] = None
    serverTime: Optional[str] = None
    
    model_config = ConfigDict(extra="ignore")
