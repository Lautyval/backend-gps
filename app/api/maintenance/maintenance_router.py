from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.auth.dependencies import get_active_enterprise
from app.api.enterprise.enterprise_model import Enterprise
from app.api.maintenance.maintenance_schema import (
    MaintenanceCreate, MaintenanceResponse,
)
from app.db.gps_db import get_async_db_session
from app.api.maintenance import maintenance_repository as repository

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])

@router.get("/", response_model=List[MaintenanceResponse])
async def get_all_maintenance(enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        return await repository.get_all(db)

@router.put("/{device_id}", response_model=MaintenanceResponse)
async def upsert_maintenance(device_id: int, record_in: MaintenanceCreate, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        return await repository.upsert(db, device_id, record_in)

@router.delete("/{device_id}")
async def delete_maintenance(device_id: int, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        success = await repository.delete(db, device_id)
        if not success: 
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        return {"status": "deleted"}

