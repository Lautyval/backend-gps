from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from typing import List
from datetime import datetime

from app.auth.dependencies import get_active_enterprise
from app.api.enterprise.enterprise_model import Enterprise
from app.api.enterprise_user.enterprise_user_model import POI, MaintenanceRecord
from app.api.enterprise_user.enterprise_user_schema import (
    POICreate, POIResponse,
    MaintenanceCreate, MaintenanceResponse
)
from app.db.gps_db import get_async_db_session

router = APIRouter(prefix="/fleet", tags=["Fleet Management"])

@router.get("/pois", response_model=List[POIResponse])
async def get_pois(enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        result = await db.execute(select(POI))
        return result.scalars().all()

@router.post("/pois", response_model=POIResponse)
async def create_poi(poi_in: POICreate, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        db_poi = POI(**poi_in.model_dump())
        db.add(db_poi)
        await db.commit()
        await db.refresh(db_poi)
        return db_poi

@router.put("/pois/{poi_id}", response_model=POIResponse)
async def update_poi(poi_id: str, poi_in: POICreate, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        result = await db.execute(select(POI).where(POI.id == poi_id))
        db_poi = result.scalar_one_or_none()
        if not db_poi: raise HTTPException(status_code=404, detail="POI no encontrado")
        
        update_data = poi_in.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(db_poi, k, v)
            
        await db.commit()
        await db.refresh(db_poi)
        return db_poi

@router.delete("/pois/{poi_id}")
async def delete_poi(poi_id: str, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        result = await db.execute(select(POI).where(POI.id == poi_id))
        db_poi = result.scalar_one_or_none()
        if not db_poi: raise HTTPException(status_code=404, detail="POI no encontrado")
        await db.delete(db_poi)
        await db.commit()
        return {"status": "deleted"}

@router.get("/maintenance", response_model=List[MaintenanceResponse])
async def get_all_maintenance(enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        result = await db.execute(select(MaintenanceRecord))
        return result.scalars().all()

@router.put("/maintenance/{device_id}", response_model=MaintenanceResponse)
async def upsert_maintenance(device_id: int, record_in: MaintenanceCreate, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        result = await db.execute(select(MaintenanceRecord).where(MaintenanceRecord.device_id == device_id))
        db_rec = result.scalar_one_or_none()
        
        if db_rec:
            update_data = record_in.model_dump(exclude_unset=True)
            for k, v in update_data.items():
                setattr(db_rec, k, v)
            db_rec.updated_at = datetime.utcnow()
        else:
            db_rec = MaintenanceRecord(**record_in.model_dump())
            db_rec.device_id = device_id
            
        db.add(db_rec)
        await db.commit()
        await db.refresh(db_rec)
        return db_rec

@router.delete("/maintenance/{device_id}")
async def delete_maintenance(device_id: int, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        result = await db.execute(select(MaintenanceRecord).where(MaintenanceRecord.device_id == device_id))
        db_rec = result.scalar_one_or_none()
        if not db_rec: raise HTTPException(status_code=404, detail="Registro no encontrado")
        await db.delete(db_rec)
        await db.commit()
        return {"status": "deleted"}

