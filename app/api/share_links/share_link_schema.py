from pydantic import BaseModel as PydanticBase

class ShareTokenRequest(PydanticBase):
    device_id: int
    expires_hours: int = 24

class ShareTokenResponse(PydanticBase):
    token: str
    url: str
    device_id: int
    expires_at: str
