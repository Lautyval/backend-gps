from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.devices.device_model import Device
from app.api.devices.device_schema import DeviceCreate, DeviceUpdate
from typing import List, Optional
from app.utils.logger_config import logger

async def get_all(db: AsyncSession) -> List[Device]:
    try:
        result = await db.execute(select(Device))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise e

async def get_by_id(db: AsyncSession, id: int) -> Optional[Device]:
    try:
        result = await db.execute(select(Device).where(Device.id == id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting device {id}: {e}")
        raise e

async def get_by_traccar_id(db: AsyncSession, traccar_id: int) -> Optional[Device]:
    try:
        result = await db.execute(select(Device).where(Device.traccar_device_id == traccar_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting device by traccar_id {traccar_id}: {e}")
        raise e

async def create(db: AsyncSession, device_in: DeviceCreate) -> Device:
    try:
        db_device = Device(**device_in.model_dump())
        db.add(db_device)
        await db.commit()
        await db.refresh(db_device)
        return db_device
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating device: {e}")
        raise e

async def update(db: AsyncSession, id: int, device_in: DeviceUpdate) -> Optional[Device]:
    try:
        db_device = await get_by_id(db, id)
        if not db_device:
            return None
        
        update_data = device_in.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(db_device, k, v)
        
        await db.commit()
        await db.refresh(db_device)
        return db_device
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating device {id}: {e}")
        raise e

async def delete(db: AsyncSession, id: int) -> bool:
    try:
        db_device = await get_by_id(db, id)
        if not db_device:
            return False
        
        await db.delete(db_device)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting device {id}: {e}")
        raise e
