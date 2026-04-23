from fastapi import Depends, APIRouter
from app.auth.dependencies import get_active_enterprise
from app.api.enterprise.enterprise_model import Enterprise
from app.api.share_links.share_link_schema import ShareTokenRequest, ShareTokenResponse
from app.api.share_links import share_links_repository as repository

router = APIRouter(prefix="/share", tags=["Share Links"])

@router.post("/share", response_model=ShareTokenResponse)
async def create_share_token(req: ShareTokenRequest, enterprise: Enterprise = Depends(get_active_enterprise)):
    return await repository.create_share_token(req)


