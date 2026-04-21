from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class EnterpriseBase(BaseModel):
    name: str
    description: Optional[str] = None
    alive: bool = True

class EnterpriseCreate(EnterpriseBase):
    pass

class EnterpriseResponse(EnterpriseBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
