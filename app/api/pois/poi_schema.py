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