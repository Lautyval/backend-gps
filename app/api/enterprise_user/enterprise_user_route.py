from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.auth.dependencies import get_main_session, get_current_user
from app.api.enterprise_user.enterprise_user_schema import (
    EnterpriseUserLinkResponse, EnterpriseUserLinkCreate, EnterpriseUserLinkUpdate
)
from app.api.enterprise_user import enterprise_user_repository as repository

router = APIRouter(prefix="/enterprise-users", tags=["Enterprise Users"])

@router.get("/enterprise/{enterprise_id}", response_model=List[EnterpriseUserLinkResponse])
async def list_users_by_enterprise(
    enterprise_id: int,
    session: AsyncSession = Depends(get_main_session),
    current_payload: dict = Depends(get_current_user)
):
    return await repository.get_users_by_enterprise(session, enterprise_id)

@router.get("/user/{user_id}", response_model=List[EnterpriseUserLinkResponse])
async def list_enterprises_by_user(
    user_id: int,
    session: AsyncSession = Depends(get_main_session),
    current_payload: dict = Depends(get_current_user)
):
    return await repository.get_enterprises_by_user(session, user_id)

@router.post("/", response_model=EnterpriseUserLinkResponse)
async def link_user_to_enterprise(
    link_in: EnterpriseUserLinkCreate,
    session: AsyncSession = Depends(get_main_session),
    current_payload: dict = Depends(get_current_user)
):
    return await repository.create_link(session, link_in)

@router.put("/{link_id}", response_model=EnterpriseUserLinkResponse)
async def update_user_link(
    link_id: int,
    link_in: EnterpriseUserLinkUpdate,
    session: AsyncSession = Depends(get_main_session),
    current_payload: dict = Depends(get_current_user)
):
    db_link = await repository.update_link(session, link_id, link_in)
    if not db_link:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    return db_link

@router.delete("/{link_id}")
async def unlink_user_from_enterprise(
    link_id: int,
    session: AsyncSession = Depends(get_main_session),
    current_payload: dict = Depends(get_current_user)
):
    success = await repository.delete_link(session, link_id)
    if not success:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    return {"status": "unlinked"}
