from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Dict, Any, List

class DriverBase(BaseModel):
    traccar_driver_id: Optional[int] = None
    name: str
    uniqueId: str = Field(alias="unique_id", serialization_alias="uniqueId")
    attributes: Optional[Dict[str, Any]] = None
    disabled: bool = False
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    traccar_driver_id: Optional[int] = None
    name: Optional[str] = None
    uniqueId: Optional[str] = Field(None, alias="unique_id", serialization_alias="uniqueId")
    attributes: Optional[Dict[str, Any]] = None
    disabled: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class DriverResponse(DriverBase):
    id: int
    created_at: datetime
    assigned_vehicle_ids: List[str] = []


