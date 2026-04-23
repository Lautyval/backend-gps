from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.user.user_model import User
from app.api.user.user_schema import UserCreate, UserUpdate
from typing import Optional
from datetime import datetime, timezone, timedelta
from app.utils.logger_config import logger

async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
    try:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {e}")
        raise e

async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting user by id {user_id}: {e}")
        raise e

async def create(db: AsyncSession, user_in: UserCreate, hashed_password: str) -> User:
    try:
        new_user = User(
            name=user_in.name,
            email=user_in.email,
            password=hashed_password,
            # Por defecto damos 7 días de expiración si no se especifica
            expiration_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7),
            alive=True
        )
        db.add(new_user)
        await db.flush()
        
        # Vincular automáticamente a la empresa demo (siempre es ID 1)
        from app.api.enterprise_user.enterprise_user_model import EnterpriseUserLink
        
        # Simplemente creamos el link con ID 1
        link = EnterpriseUserLink(
            enterprise_id=1,
            user_id=new_user.id,
            role="user"
        )
        db.add(link)
        
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating user: {e}")
        raise e

async def update(db: AsyncSession, user_id: int, user_in: UserUpdate, hashed_password: Optional[str] = None) -> Optional[User]:
    try:
        db_user = await get_by_id(db, user_id)
        if not db_user:
            return None
        
        update_data = user_in.model_dump(exclude_unset=True)
        if 'password' in update_data:
            del update_data['password']
            if hashed_password:
                db_user.password = hashed_password
                
        for k, v in update_data.items():
            setattr(db_user, k, v)
            
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating user {user_id}: {e}")
        raise e

async def deactivate(db: AsyncSession, user_id: int) -> bool:
    try:
        db_user = await get_by_id(db, user_id)
        if not db_user:
            return False
        
        db_user.alive = False
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deactivating user {user_id}: {e}")
        raise e


