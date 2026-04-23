from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class EnterpriseBase(BaseModel):
    name: str
    fullname: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    disabled: bool = False

class EnterpriseCreate(EnterpriseBase):
    pass

class EnterpriseUpdate(BaseModel):
    name: Optional[str] = None
    fullname: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    disabled: Optional[bool] = None

class EnterpriseResponse(EnterpriseBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

