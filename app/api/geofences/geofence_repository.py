from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.geofences.geofence_model import Geofence
from app.api.geofences.geofence_schema import GeofenceCreate, GeofenceUpdate
from typing import List, Optional
from app.utils.logger_config import logger

async def get_all(db: AsyncSession) -> List[Geofence]:
    try:
        result = await db.execute(select(Geofence))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting geofences: {e}")
        raise e

async def get_by_id(db: AsyncSession, id: int) -> Optional[Geofence]:
    try:
        result = await db.execute(select(Geofence).where(Geofence.id == id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting geofence {id}: {e}")
        raise e

async def create(db: AsyncSession, geofence_in: GeofenceCreate) -> Geofence:
    try:
        db_geofence = Geofence(**geofence_in.model_dump())
        db.add(db_geofence)
        await db.commit()
        await db.refresh(db_geofence)
        return db_geofence
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating geofence: {e}")
        raise e

async def update(db: AsyncSession, id: int, geofence_in: GeofenceUpdate) -> Optional[Geofence]:
    try:
        db_geofence = await get_by_id(db, id)
        if not db_geofence:
            return None
        
        update_data = geofence_in.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(db_geofence, k, v)
        
        await db.commit()
        await db.refresh(db_geofence)
        return db_geofence
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating geofence {id}: {e}")
        raise e

async def delete(db: AsyncSession, id: int) -> bool:
    try:
        db_geofence = await get_by_id(db, id)
        if not db_geofence:
            return False
        
        await db.delete(db_geofence)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting geofence {id}: {e}")
        raise e
