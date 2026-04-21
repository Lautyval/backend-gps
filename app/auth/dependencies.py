from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from app.auth.jwt_handler import decode_access_token
from app.db.main_db import AsyncSessionMain

bearer_scheme = HTTPBearer()

async def get_main_session():
    async with AsyncSessionMain() as session:
        yield session

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return payload

async def get_active_enterprise(
    current_payload: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_main_session)
):
    from app.api.user.user_model import User
    from app.api.enterprise.enterprise_model import Enterprise
    
    user_id = int(current_payload["sub"])
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.enterprises:
        raise HTTPException(status_code=403, detail="Sin empresa asignada.")
    
    return user.enterprises[0]
