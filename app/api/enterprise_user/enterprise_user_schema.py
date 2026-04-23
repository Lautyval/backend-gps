from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class EnterpriseUserLinkBase(BaseModel):
    enterprise_id: int
    user_id: int
    role: Optional[str] = None

class EnterpriseUserLinkCreate(EnterpriseUserLinkBase):
    pass

class EnterpriseUserLinkUpdate(BaseModel):
    role: Optional[str] = None

class EnterpriseUserLinkResponse(EnterpriseUserLinkBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

