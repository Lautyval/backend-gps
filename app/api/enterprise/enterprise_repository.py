from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.enterprise.enterprise_model import Enterprise
from app.api.enterprise.enterprise_schema import EnterpriseCreate, EnterpriseUpdate
from typing import List, Optional
from app.utils.logger_config import logger

async def get_all(db: AsyncSession, include_disabled: bool = False) -> List[Enterprise]:
    try:
        query = select(Enterprise)
        if not include_disabled:
            query = query.where(Enterprise.disabled == False)
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting enterprises: {e}")
        raise e

async def get_by_id(db: AsyncSession, enterprise_id: int) -> Optional[Enterprise]:
    try:
        result = await db.execute(select(Enterprise).where(Enterprise.id == enterprise_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting enterprise {enterprise_id}: {e}")
        raise e

async def create(db: AsyncSession, enterprise_in: EnterpriseCreate) -> Enterprise:
    try:
        db_enterprise = Enterprise(**enterprise_in.model_dump())
        db.add(db_enterprise)
        await db.commit()
        await db.refresh(db_enterprise)
        return db_enterprise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating enterprise: {e}")
        raise e

async def update(db: AsyncSession, enterprise_id: int, enterprise_in: EnterpriseUpdate) -> Optional[Enterprise]:
    try:
        db_enterprise = await get_by_id(db, enterprise_id)
        if not db_enterprise:
            return None
        
        update_data = enterprise_in.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(db_enterprise, k, v)
        
        await db.commit()
        await db.refresh(db_enterprise)
        return db_enterprise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating enterprise {enterprise_id}: {e}")
        raise e

async def deactivate(db: AsyncSession, enterprise_id: int) -> bool:
    try:
        db_enterprise = await get_by_id(db, enterprise_id)
        if not db_enterprise:
            return False
        
        db_enterprise.disabled = True
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deactivating enterprise {enterprise_id}: {e}")
        raise e

