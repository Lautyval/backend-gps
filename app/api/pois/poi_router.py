from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.auth.dependencies import get_active_enterprise
from app.api.enterprise.enterprise_model import Enterprise
from app.api.pois.poi_schema import POICreate, POIResponse
from app.db.gps_db import get_async_db_session
from app.api.pois import poi_repository as repository

router = APIRouter(prefix="/pois", tags=["POIs"])

@router.get("/", response_model=List[POIResponse])
async def get_pois(enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        return await repository.get_all(db)

@router.post("/", response_model=POIResponse)
async def create_poi(poi_in: POICreate, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        return await repository.create(db, poi_in)

@router.put("/{poi_id}", response_model=POIResponse)
async def update_poi(poi_id: str, poi_in: POICreate, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        db_poi = await repository.update(db, poi_id, poi_in)
        if not db_poi: 
            raise HTTPException(status_code=404, detail="POI no encontrado")
        return db_poi

@router.delete("/{poi_id}")
async def delete_poi(poi_id: str, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        success = await repository.delete(db, poi_id)
        if not success: 
            raise HTTPException(status_code=404, detail="POI no encontrado")
        return {"status": "deleted"}