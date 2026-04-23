from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class MaintenanceBase(BaseModel):
    serviceName: str
    intervalDays: int
    intervalKm: int = 10000
    lastServiceDate: str
    lastServiceKm: float = 0
    alertStrategy: str = 'both'
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class MaintenanceCreate(MaintenanceBase):
    device_id: int

class MaintenanceResponse(MaintenanceBase):
    device_id: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
