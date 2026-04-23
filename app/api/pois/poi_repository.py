from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.pois.poi_model import POI
from app.api.pois.poi_schema import POICreate
from typing import List, Optional
from app.utils.logger_config import logger

async def get_all(db: AsyncSession) -> List[POI]:
    try:
        result = await db.execute(select(POI))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting POIs: {e}")
        raise e

async def get_by_id(db: AsyncSession, poi_id: str) -> Optional[POI]:
    try:
        result = await db.execute(select(POI).where(POI.id == poi_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting POI {poi_id}: {e}")
        raise e

async def create(db: AsyncSession, poi_in: POICreate) -> POI:
    try:
        db_poi = POI(**poi_in.model_dump())
        db.add(db_poi)
        await db.commit()
        await db.refresh(db_poi)
        return db_poi
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating POI: {e}")
        raise e

async def update(db: AsyncSession, poi_id: str, poi_in: POICreate) -> Optional[POI]:
    try:
        db_poi = await get_by_id(db, poi_id)
        if not db_poi:
            return None
        
        update_data = poi_in.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(db_poi, k, v)
            
        await db.commit()
        await db.refresh(db_poi)
        return db_poi
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating POI {poi_id}: {e}")
        raise e

async def delete(db: AsyncSession, poi_id: str) -> bool:
    try:
        db_poi = await get_by_id(db, poi_id)
        if not db_poi:
            return False
        
        await db.delete(db_poi)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting POI {poi_id}: {e}")
        raise e

