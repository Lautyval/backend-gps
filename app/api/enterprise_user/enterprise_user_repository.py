from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.enterprise_user.enterprise_user_model import EnterpriseUserLink
from app.api.enterprise_user.enterprise_user_schema import EnterpriseUserLinkCreate, EnterpriseUserLinkUpdate
from typing import List, Optional
from app.utils.logger_config import logger

async def get_users_by_enterprise(db: AsyncSession, enterprise_id: int) -> List[EnterpriseUserLink]:
    try:
        result = await db.execute(
            select(EnterpriseUserLink).where(EnterpriseUserLink.enterprise_id == enterprise_id)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting users for enterprise {enterprise_id}: {e}")
        raise e

async def get_enterprises_by_user(db: AsyncSession, user_id: int) -> List[EnterpriseUserLink]:
    try:
        result = await db.execute(
            select(EnterpriseUserLink).where(EnterpriseUserLink.user_id == user_id)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting enterprises for user {user_id}: {e}")
        raise e

async def create_link(db: AsyncSession, link_in: EnterpriseUserLinkCreate) -> EnterpriseUserLink:
    try:
        db_link = EnterpriseUserLink(**link_in.model_dump())
        db.add(db_link)
        await db.commit()
        await db.refresh(db_link)
        return db_link
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating enterprise user link: {e}")
        raise e

async def update_link(db: AsyncSession, link_id: int, link_in: EnterpriseUserLinkUpdate) -> Optional[EnterpriseUserLink]:
    try:
        result = await db.execute(
            select(EnterpriseUserLink).where(EnterpriseUserLink.id == link_id)
        )
        db_link = result.scalar_one_or_none()
        if not db_link:
            return None
        
        if link_in.role is not None:
            db_link.role = link_in.role
        
        await db.commit()
        await db.refresh(db_link)
        return db_link
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating link {link_id}: {e}")
        raise e

async def delete_link(db: AsyncSession, link_id: int) -> bool:
    try:
        result = await db.execute(
            select(EnterpriseUserLink).where(EnterpriseUserLink.id == link_id)
        )
        db_link = result.scalar_one_or_none()
        if not db_link:
            return False
        
        await db.delete(db_link)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting link {link_id}: {e}")
        raise e

