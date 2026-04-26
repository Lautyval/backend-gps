from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class DeviceBase(BaseModel):
    name: str
    unique_id: str
    disabled: bool = False

class DeviceCreate(DeviceBase):
    traccar_device_id: Optional[int] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    unique_id: Optional[str] = None
    traccar_device_id: Optional[int] = None
    disabled: Optional[bool] = None

class DeviceResponse(DeviceBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

