from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

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
