import os, time
from jose import jwt
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.share_links.share_link_schema import ShareTokenRequest, ShareTokenResponse
from app.api.share_links.share_link_model import ShareLink
from app.utils.logger_config import logger

_JWT_SECRET = os.getenv("JWT_SECRET")
_ALGO = os.getenv("ALGORITHM")
_PUBLIC_URL = os.getenv("PUBLIC_URL")

async def create_share_token(db: AsyncSession, req: ShareTokenRequest, enterprise_id: int) -> ShareTokenResponse:
    try:
        exp = int(time.time()) + req.expires_hours * 3600
        payload = {
            "device_id": req.device_id, 
            "exp": exp, 
            "type": "share",
            "ent": enterprise_id
        }
        token = jwt.encode(payload, _JWT_SECRET, algorithm=_ALGO)
        url = f"{_PUBLIC_URL}/?track={token}"

        
        expires_at = datetime.utcfromtimestamp(exp)
        
        # Save to database
        db_link = ShareLink(
            token=token,
            device_id=req.device_id,
            expires_at=expires_at,
            revoked=False
        )
        db.add(db_link)
        await db.commit()
        
        return ShareTokenResponse(
            token=token,
            url=url,
            device_id=req.device_id,
            expires_at=expires_at.isoformat()
        )
    except Exception as e:
        logger.error(f"Error creating share token: {e}")
        raise e

async def revoke_share_token(db: AsyncSession, token: str) -> bool:
    try:
        result = await db.execute(
            select(ShareLink).where(ShareLink.token == token)
        )
        db_link = result.scalar_one_or_none()
        if db_link:
            db_link.revoked = True
            await db.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error revoking share token: {e}")
        await db.rollback()
        return False

async def is_token_revoked(db: AsyncSession, token: str) -> bool:
    try:
        result = await db.execute(
            select(ShareLink).where(ShareLink.token == token)
        )
        db_link = result.scalar_one_or_none()
        return db_link.revoked if db_link else True # If not found, assume revoked
    except Exception:
        return True


