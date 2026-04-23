from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.drivers.driver_model import Driver
from app.api.drivers.driver_schema import DriverCreate, DriverUpdate
from typing import List, Optional
from app.utils.logger_config import logger

async def get_all(db: AsyncSession) -> List[Driver]:
    try:
        result = await db.execute(select(Driver))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting drivers: {e}")
        raise e

async def get_by_id(db: AsyncSession, driver_id: int) -> Optional[Driver]:
    try:
        result = await db.execute(select(Driver).where(Driver.id == driver_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting driver {driver_id}: {e}")
        raise e

async def create(db: AsyncSession, driver_in: DriverCreate) -> Driver:
    try:
        db_driver = Driver(**driver_in.model_dump())
        db.add(db_driver)
        await db.commit()
        await db.refresh(db_driver)
        return db_driver
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating driver: {e}")
        raise e

async def update(db: AsyncSession, driver_id: int, driver_in: DriverUpdate) -> Optional[Driver]:
    try:
        db_driver = await get_by_id(db, driver_id)
        if not db_driver:
            return None
        
        update_data = driver_in.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(db_driver, k, v)
            
        await db.commit()
        await db.refresh(db_driver)
        return db_driver
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating driver {driver_id}: {e}")
        raise e

async def delete(db: AsyncSession, driver_id: int) -> bool:
    try:
        db_driver = await get_by_id(db, driver_id)
        if not db_driver:
            return False
        
        await db.delete(db_driver)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting driver {driver_id}: {e}")
        raise e
