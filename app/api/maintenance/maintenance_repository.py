from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.api.maintenance.maintenance_model import MaintenanceRecord
from app.api.maintenance.maintenance_schema import MaintenanceCreate
from typing import List, Optional
from app.utils.logger_config import logger

async def get_all(db: AsyncSession) -> List[MaintenanceRecord]:
    try:
        result = await db.execute(select(MaintenanceRecord))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting maintenance records: {e}")
        raise e

async def get_by_device_id(db: AsyncSession, device_id: int) -> Optional[MaintenanceRecord]:
    try:
        result = await db.execute(select(MaintenanceRecord).where(MaintenanceRecord.device_id == device_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting maintenance for device {device_id}: {e}")
        raise e

async def upsert(db: AsyncSession, device_id: int, record_in: MaintenanceCreate) -> MaintenanceRecord:
    try:
        db_rec = await get_by_device_id(db, device_id)
        
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
    except Exception as e:
        await db.rollback()
        logger.error(f"Error upserting maintenance for device {device_id}: {e}")
        raise e

async def delete(db: AsyncSession, device_id: int) -> bool:
    try:
        db_rec = await get_by_device_id(db, device_id)
        if not db_rec:
            return False
        
        await db.delete(db_rec)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting maintenance for device {device_id}: {e}")
        raise e

