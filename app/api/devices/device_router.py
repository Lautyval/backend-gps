from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.auth.dependencies import get_active_enterprise
from app.api.enterprise.enterprise_model import Enterprise
from app.api.devices.device_schema import DeviceCreate, DeviceUpdate, DeviceResponse
from app.db.gps_db import get_async_db_session
from app.api.devices import device_repository as repository

router = APIRouter(prefix="/devices", tags=["Devices"])

@router.get("/", response_model=List[DeviceResponse])
async def list_devices(enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        return await repository.get_all(db)

@router.post("/", response_model=DeviceResponse)
async def create_device(
    device_in: DeviceCreate, 
    enterprise: Enterprise = Depends(get_active_enterprise)
):
    async with get_async_db_session(enterprise.id) as db:

        return await repository.create(db, device_in)

@router.put("/{id}", response_model=DeviceResponse)
async def update_device(
    id: int, 
    device_in: DeviceUpdate, 
    enterprise: Enterprise = Depends(get_active_enterprise)
):
    async with get_async_db_session(enterprise.id) as db:
        db_device = await repository.update(db, id, device_in)
        if not db_device:
            raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
        return db_device

@router.delete("/{id}")
async def delete_device(
    id: int, 
    enterprise: Enterprise = Depends(get_active_enterprise)
):
    async with get_async_db_session(enterprise.id) as db:
        success = await repository.delete(db, id)
        if not success:
            raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
        return {"status": "deleted"}
