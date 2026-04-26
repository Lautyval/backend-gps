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
async def create_driver(
    driver_in: DriverCreate, 
    enterprise: Enterprise = Depends(get_active_enterprise)
):
    async with get_async_db_session(enterprise.id) as db:
        return await repository.create(db, driver_in)


@router.put("/{unique_id}", response_model=DriverResponse)
async def update_driver(
    unique_id: str, 
    driver_in: DriverUpdate, 
    enterprise: Enterprise = Depends(get_active_enterprise)
):
    async with get_async_db_session(enterprise.id) as db:
        # 1. Get current driver
        db_driver = await repository.get_by_unique_id(db, unique_id)
        if not db_driver and unique_id.isdigit():
            db_driver = await repository.get_by_traccar_id(db, int(unique_id))

        if not db_driver:
            raise HTTPException(status_code=404, detail="Chofer no encontrado")

        # 2. Update via repository (which handles Traccar sync)
        return await repository.update(db, db_driver.id, driver_in)


@router.delete("/{unique_id}")
async def delete_driver(
    unique_id: str, 
    enterprise: Enterprise = Depends(get_active_enterprise)
):
    async with get_async_db_session(enterprise.id) as db:
        # 1. Resolve driver
        db_driver = await repository.get_by_unique_id(db, unique_id)
        if not db_driver and unique_id.isdigit():
            db_driver = await repository.get_by_traccar_id(db, int(unique_id))

        if not db_driver:
            raise HTTPException(status_code=404, detail="Chofer no encontrado")

        # 2. Delete via repository (which handles Traccar sync)
        success = await repository.delete(db, db_driver.id)
        if not success:
            raise HTTPException(status_code=500, detail="Error al eliminar chofer")
            
        return {"detail": "Chofer eliminado"}
