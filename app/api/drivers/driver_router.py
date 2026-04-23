from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.auth.dependencies import get_active_enterprise
from app.api.enterprise.enterprise_model import Enterprise
from app.api.drivers.driver_schema import DriverCreate, DriverResponse, DriverUpdate
from app.db.gps_db import get_async_db_session
from app.api.drivers import driver_repository as repository

router = APIRouter(prefix="/drivers", tags=["Drivers"])

@router.get("/", response_model=List[DriverResponse])
async def get_drivers(enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        return await repository.get_all(db)

@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(driver_id: int, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        db_driver = await repository.get_by_id(db, driver_id)
        if not db_driver:
            raise HTTPException(status_code=404, detail="Chofer no encontrado")
        return db_driver

@router.post("/", response_model=DriverResponse)
async def create_driver(driver_in: DriverCreate, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        return await repository.create(db, driver_in)

@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(driver_id: int, driver_in: DriverUpdate, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        db_driver = await repository.update(db, driver_id, driver_in)
        if not db_driver: 
            raise HTTPException(status_code=404, detail="Chofer no encontrado")
        return db_driver

@router.delete("/{driver_id}")
async def delete_driver(driver_id: int, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        success = await repository.delete(db, driver_id)
        if not success: 
            raise HTTPException(status_code=404, detail="Chofer no encontrado")
        return {"status": "deleted"}
