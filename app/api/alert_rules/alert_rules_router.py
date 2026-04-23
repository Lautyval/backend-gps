from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_active_enterprise
from app.api.enterprise.enterprise_model import Enterprise
from app.api.alert_rules.alert_rules_schema import (
    AlertRuleCreate, AlertRuleResponse
)
from app.db.gps_db import get_async_db_session
from typing import List
from app.api.alert_rules import alert_rules_repository as repository

router = APIRouter(prefix="/alert-rules", tags=["Alert Rules"])

@router.get("/", response_model=List[AlertRuleResponse])
async def get_alert_rules(enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        return await repository.get_all(db)

@router.post("/", response_model=AlertRuleResponse)
async def create_alert_rule(rule_in: AlertRuleCreate, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        return await repository.create(db, rule_in)

@router.put("/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(rule_id: int, rule_in: AlertRuleCreate, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        db_rule = await repository.update(db, rule_id, rule_in)
        if not db_rule: 
            raise HTTPException(status_code=404, detail="Regla no encontrada")
        return db_rule

@router.delete("/{rule_id}")
async def delete_alert_rule(rule_id: int, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        success = await repository.delete(db, rule_id)
        if not success: 
            raise HTTPException(status_code=404, detail="Regla no encontrada")
        return {"status": "deleted"}

