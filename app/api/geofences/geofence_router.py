from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.auth.dependencies import get_active_enterprise
from app.api.enterprise.enterprise_model import Enterprise
from app.api.geofences.geofence_schema import GeofenceCreate, GeofenceUpdate, GeofenceResponse
from app.db.gps_db import get_async_db_session
from app.api.geofences import geofence_repository as repository

router = APIRouter(prefix="/geofences", tags=["Geofences"])

@router.get("/", response_model=List[GeofenceResponse])
async def list_geofences(enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        return await repository.get_all(db)

@router.post("/", response_model=GeofenceResponse)
async def create_geofence(
    geofence_in: GeofenceCreate, 
    enterprise: Enterprise = Depends(get_active_enterprise)
):
    async with get_async_db_session(enterprise.id) as db:
        return await repository.create(db, geofence_in)


@router.put("/{id}", response_model=GeofenceResponse)
async def update_geofence(
    id: int, 
    geofence_in: GeofenceUpdate, 
    enterprise: Enterprise = Depends(get_active_enterprise)
):
    async with get_async_db_session(enterprise.id) as db:
        db_geofence = await repository.update(db, id, geofence_in)
        if not db_geofence:
            raise HTTPException(status_code=404, detail="Geocerca no encontrada")
        return db_geofence

@router.delete("/{id}")
async def delete_geofence(
    id: int, 
    enterprise: Enterprise = Depends(get_active_enterprise)
):
    async with get_async_db_session(enterprise.id) as db:
        success = await repository.delete(db, id)
        if not success:
            raise HTTPException(status_code=404, detail="Geocerca no encontrada")
        return {"status": "deleted"}
