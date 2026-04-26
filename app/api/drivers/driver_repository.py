from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.drivers.driver_model import Driver
from app.api.drivers.driver_schema import DriverCreate, DriverUpdate
from typing import List, Optional
from app.utils.logger_config import logger
from app.api.traccar.services import TraccarService
from app.api.traccar.schema import DriverCreate as TraccarDriverCreate, DriverUpdate as TraccarDriverUpdate

async def _populate_links(db: AsyncSession, db_driver: Optional[Driver]):
    if not db_driver:
        return None
    from app.api.drivers.driver_device_model import DriverDeviceLink
    links_res = await db.execute(
        select(DriverDeviceLink.device_unique_id).where(DriverDeviceLink.driver_unique_id == db_driver.unique_id)
    )
    db_driver.assigned_vehicle_ids = [row[0] for row in links_res.all()]
    return db_driver

async def get_all(db: AsyncSession) -> List[Driver]:
    try:
        result = await db.execute(select(Driver))
        drivers = result.scalars().all()
        for d in drivers:
            await _populate_links(db, d)
        return drivers
    except Exception as e:
        logger.error(f"Error getting drivers: {e}")
        raise e

async def get_by_id(db: AsyncSession, driver_id: int) -> Optional[Driver]:
    try:
        result = await db.execute(select(Driver).where(Driver.id == driver_id))
        db_driver = result.scalar_one_or_none()
        return await _populate_links(db, db_driver)
    except Exception as e:
        logger.error(f"Error getting driver {driver_id}: {e}")
        raise e

async def get_by_unique_id(db: AsyncSession, unique_id: str) -> Optional[Driver]:
    try:
        result = await db.execute(select(Driver).where(Driver.unique_id == unique_id))
        db_driver = result.scalar_one_or_none()
        return await _populate_links(db, db_driver)
    except Exception as e:
        logger.error(f"Error getting driver by unique_id {unique_id}: {e}")
        raise e

async def get_by_traccar_id(db: AsyncSession, traccar_id: int) -> Optional[Driver]:
    try:
        result = await db.execute(select(Driver).where(Driver.traccar_driver_id == traccar_id))
        db_driver = result.scalar_one_or_none()
        return await _populate_links(db, db_driver)
    except Exception as e:
        logger.error(f"Error getting driver by traccar_id {traccar_id}: {e}")
        raise e


async def create(db: AsyncSession, driver_in: DriverCreate) -> Driver:
    try:
        # 1. Sync with Traccar if no traccar_driver_id provided
        if driver_in.traccar_driver_id is None:
            traccar = TraccarService()
            try:
                traccar_drv = await traccar.create_driver(TraccarDriverCreate(
                    name=driver_in.name,
                    uniqueId=driver_in.uniqueId
                ))
                driver_in.traccar_driver_id = traccar_drv.id
            except Exception as e:
                logger.error(f"Error creating driver in Traccar: {e}")
                raise Exception(f"Error al registrar chofer en Traccar: {e}")

        # 2. Save to Postgres
        db_driver = Driver(**driver_in.model_dump(by_alias=True))
        db.add(db_driver)
        await db.commit()
        await db.refresh(db_driver)
        
        # 3. Load links
        return await _populate_links(db, db_driver)


    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating driver: {e}")
        raise e

async def update(db: AsyncSession, driver_id: int, driver_in: DriverUpdate) -> Optional[Driver]:
    try:
        db_driver = await get_by_id(db, driver_id)
        if not db_driver:
            return None
        
        # 1. Sync with Traccar if relevant fields changed
        if driver_in.name or driver_in.uniqueId or driver_in.disabled is not None:
            traccar = TraccarService()
            try:
                await traccar.update_driver(db_driver.traccar_driver_id, TraccarDriverUpdate(
                    name=driver_in.name if driver_in.name else db_driver.name,
                    uniqueId=driver_in.uniqueId if driver_in.uniqueId else db_driver.unique_id
                ))
            except Exception as e:
                logger.warning(f"Error synchronizing driver update with Traccar: {e}")



        # 2. Update local database
        update_data = driver_in.model_dump(exclude_unset=True, by_alias=True)
        for k, v in update_data.items():
            setattr(db_driver, k, v)
            
        await db.commit()
        await db.refresh(db_driver)

        # 3. Load links
        return await _populate_links(db, db_driver)


    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating driver {driver_id}: {e}")
        raise e

async def delete(db: AsyncSession, driver_id: int) -> bool:
    try:
        db_driver = await get_by_id(db, driver_id)
        if not db_driver:
            return False
        
        # Sync delete with Traccar if possible
        try:
            traccar = TraccarService()
            await traccar.delete_driver(db_driver.traccar_driver_id)
        except Exception as e:
            logger.warning(f"Error deleting driver from Traccar: {e}")

        await db.delete(db_driver)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting driver {driver_id}: {e}")
        raise e
