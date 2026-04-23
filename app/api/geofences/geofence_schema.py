from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class GeofenceBase(BaseModel):
    name: str
    description: Optional[str] = None
    traccar_geofence_id: int


class GeofenceCreate(GeofenceBase):
    pass

class GeofenceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    traccar_geofence_id: Optional[int] = None

class GeofenceResponse(GeofenceBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
