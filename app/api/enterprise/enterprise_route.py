from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.auth.dependencies import get_main_session, get_current_user
from app.api.enterprise.enterprise_schema import EnterpriseResponse, EnterpriseCreate, EnterpriseUpdate
from app.api.enterprise import enterprise_repository as repository

router = APIRouter(prefix="/enterprises", tags=["Enterprise"])

@router.get("/", response_model=List[EnterpriseResponse])
async def list_enterprises(
    session: AsyncSession = Depends(get_main_session),
    current_payload: dict = Depends(get_current_user)
):
    return await repository.get_all(session)

@router.post("/", response_model=EnterpriseResponse)
async def create_enterprise(
    enterprise_in: EnterpriseCreate,
    session: AsyncSession = Depends(get_main_session),
    current_payload: dict = Depends(get_current_user)
):
    return await repository.create(session, enterprise_in)

@router.put("/{enterprise_id}", response_model=EnterpriseResponse)
async def update_enterprise(
    enterprise_id: int,
    enterprise_in: EnterpriseUpdate,
    session: AsyncSession = Depends(get_main_session),
    current_payload: dict = Depends(get_current_user)
):
    db_enterprise = await repository.update(session, enterprise_id, enterprise_in)
    if not db_enterprise:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return db_enterprise

@router.delete("/{enterprise_id}")
async def delete_enterprise(
    enterprise_id: int,
    session: AsyncSession = Depends(get_main_session),
    current_payload: dict = Depends(get_current_user)
):
    success = await repository.deactivate(session, enterprise_id)
    if not success:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return {"status": "deactivated"}

