from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class POIBase(BaseModel):
    id: str
    name: str
    category: str
    lat: float
    lng: float
    color: str
    notes: Optional[str] = None

class POICreate(POIBase):
    pass

class POIResponse(POIBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MaintenanceBase(BaseModel):
    serviceName: str
    intervalDays: int
    lastServiceDate: str
    notes: Optional[str] = None

class MaintenanceCreate(MaintenanceBase):
    device_id: int

class MaintenanceResponse(MaintenanceBase):
    device_id: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
