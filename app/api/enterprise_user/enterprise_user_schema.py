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

class AlertRuleBase(BaseModel):
    name: str
    device_id: Optional[int] = None
    condition: str
    threshold: Optional[float] = None
    active: bool = True

class AlertRuleCreate(AlertRuleBase):
    pass

class AlertRuleResponse(AlertRuleBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
