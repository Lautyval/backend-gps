from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.auth.dependencies import get_active_enterprise
from app.api.enterprise.enterprise_model import Enterprise
from app.api.devices.device_schema import DeviceCreate, DeviceUpdate, DeviceResponse
from app.db.gps_db import get_async_db_session
from app.api.devices import device_repository as repository

from app.api.traccar.services import TraccarService
from app.api.traccar.schema import DeviceUpdate as TraccarDeviceUpdate, DriverUpdate as TraccarDriverUpdate
from app.api.traccar.schema import DeviceCreate as TraccarDeviceCreate

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
    # Register in Traccar automatically if not provided
    if device_in.traccar_device_id is None:
        traccar = TraccarService()
        try:
            traccar_dev = await traccar.create_device(TraccarDeviceCreate(
                name=device_in.name,
                uniqueId=device_in.unique_id
            ))
            device_in.traccar_device_id = traccar_dev.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al registrar en Traccar: {str(e)}")

    async with get_async_db_session(enterprise.id) as db:
        return await repository.create(db, device_in)


@router.put("/{unique_id}", response_model=DeviceResponse)
async def update_device(
    unique_id: str, 
    device_in: DeviceUpdate, 
    enterprise: Enterprise = Depends(get_active_enterprise)
):
    async with get_async_db_session(enterprise.id) as db:
        # 1. Get current device from Postgres by unique_id (with fallback to Traccar ID)
        db_device = await repository.get_by_unique_id(db, unique_id)
        if not db_device and unique_id.isdigit():
            db_device = await repository.get_by_traccar_id(db, int(unique_id))
            
        if not db_device:
            raise HTTPException(status_code=404, detail="Dispositivo no encontrado")


        # 2. Sync with Traccar if name or unique_id changed
        if device_in.name or device_in.unique_id:
            traccar = TraccarService()
            try:
                await traccar.update_device(db_device.traccar_device_id, TraccarDeviceUpdate(
                    name=device_in.name if device_in.name else db_device.name,
                    uniqueId=device_in.unique_id if device_in.unique_id else db_device.unique_id,
                    disabled=device_in.disabled if device_in.disabled is not None else db_device.disabled
                ))

            except Exception as e:
                # Log the error but don't fail the entire request if Traccar sync fails
                print(f"Error synchronizing update with Traccar: {e}")


        # 3. Update local database
        return await repository.update(db, db_device.id, device_in)


@router.delete("/{unique_id}")
async def delete_device(
    unique_id: str, 
    enterprise: Enterprise = Depends(get_active_enterprise)
):
    async with get_async_db_session(enterprise.id) as db:
        # 1. Get device from Postgres by unique_id (with fallback to Traccar ID)
        db_device = await repository.get_by_unique_id(db, unique_id)
        if not db_device and unique_id.isdigit():
            db_device = await repository.get_by_traccar_id(db, int(unique_id))

        if not db_device:
            raise HTTPException(status_code=404, detail="Dispositivo no encontrado")


        # 2. Delete from Traccar
        traccar = TraccarService()
        try:
            await traccar.delete_device(db_device.traccar_device_id)
        except Exception as e:
            # Log error but proceed with local deletion
            print(f"Error deleting from Traccar: {e}")

        # 3. Delete from local database
        success = await repository.delete(db, db_device.id)
        if not success:
            raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
        return {"status": "deleted"}


