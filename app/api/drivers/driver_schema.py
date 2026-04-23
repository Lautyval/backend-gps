from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any

class DriverBase(BaseModel):
    traccar_driver_id: Optional[int] = None
    name: str
    unique_id: str
    attributes: Optional[Dict[str, Any]] = None
    disabled: bool = False

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    traccar_driver_id: Optional[int] = None
    name: Optional[str] = None
    unique_id: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    disabled: Optional[bool] = None

class DriverResponse(DriverBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
