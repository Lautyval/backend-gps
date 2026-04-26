from fastapi import Depends, APIRouter, HTTPException
from app.auth.dependencies import get_active_enterprise
from app.api.enterprise.enterprise_model import Enterprise
from app.api.share_links.share_link_schema import ShareTokenRequest, ShareTokenResponse
from app.api.share_links import share_links_repository as repository
from app.db.gps_db import get_async_db_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/share", tags=["Share Links"])

@router.post("/share", response_model=ShareTokenResponse)
async def create_share_token(req: ShareTokenRequest, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        return await repository.create_share_token(db, req, enterprise.id)


@router.delete("/share/{token}")
async def revoke_share_token(token: str, enterprise: Enterprise = Depends(get_active_enterprise)):
    async with get_async_db_session(enterprise.id) as db:
        success = await repository.revoke_share_token(db, token)
        if not success:
            raise HTTPException(status_code=404, detail="Token no encontrado o ya revocado")
        return {"status": "revoked"}



