from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: EmailStr
    expiration_date: Optional[datetime] = None
    alive: bool = True

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    enterprise_id: Optional[int] = Field(alias="enterprise_id", default=None)
    enterprise: str = Field(alias="enterprise_name", default="N/A")
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    expiration_date: Optional[datetime] = None
    alive: Optional[bool] = None

class Token(BaseModel):

    access_token: str
    token_type: str
    user: dict

class UserLogin(BaseModel):
    email: str = Field(example="ejemplo@keuken.com")
    password: str = Field(example="contraseniasegura123")