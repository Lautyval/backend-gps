from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.auth.dependencies import get_main_session, get_current_user
from app.api.enterprise.enterprise_model import Enterprise
from app.api.enterprise.enterprise_schema import EnterpriseResponse

router = APIRouter(prefix="/enterprises", tags=["Enterprise"])

@router.get("/", response_model=List[EnterpriseResponse])
async def list_enterprises(
    session: AsyncSession = Depends(get_main_session),
    current_payload: dict = Depends(get_current_user)
):
    result = await session.execute(select(Enterprise))
    return result.scalars().all()
