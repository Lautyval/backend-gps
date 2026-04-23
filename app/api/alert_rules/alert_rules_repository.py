from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.alert_rules.alert_rules_model import AlertRule
from app.api.alert_rules.alert_rules_schema import AlertRuleCreate
from typing import List, Optional
from app.utils.logger_config import logger

async def get_all(db: AsyncSession) -> List[AlertRule]:
    try:
        result = await db.execute(select(AlertRule).order_by(AlertRule.created_at.desc()))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting alert rules: {e}")
        raise e

async def get_by_id(db: AsyncSession, rule_id: int) -> Optional[AlertRule]:
    try:
        result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting alert rule {rule_id}: {e}")
        raise e

async def create(db: AsyncSession, rule_in: AlertRuleCreate) -> AlertRule:
    try:
        db_rule = AlertRule(**rule_in.model_dump())
        db.add(db_rule)
        await db.commit()
        await db.refresh(db_rule)
        return db_rule
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating alert rule: {e}")
        raise e

async def update(db: AsyncSession, rule_id: int, rule_in: AlertRuleCreate) -> Optional[AlertRule]:
    try:
        db_rule = await get_by_id(db, rule_id)
        if not db_rule:
            return None
        
        for k, v in rule_in.model_dump().items():
            setattr(db_rule, k, v)
        
        await db.commit()
        await db.refresh(db_rule)
        return db_rule
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating alert rule {rule_id}: {e}")
        raise e

async def delete(db: AsyncSession, rule_id: int) -> bool:
    try:
        db_rule = await get_by_id(db, rule_id)
        if not db_rule:
            return False
        
        await db.delete(db_rule)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting alert rule {rule_id}: {e}")
        raise e

