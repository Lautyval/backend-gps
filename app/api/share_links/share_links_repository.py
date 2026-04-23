import os, time
from jose import jwt
from datetime import datetime
from app.api.share_links.share_link_schema import ShareTokenRequest, ShareTokenResponse
from app.utils.logger_config import logger

_JWT_SECRET = os.getenv("JWT_SECRET")
_ALGO = os.getenv("ALGORITHM")
_PUBLIC_URL = os.getenv("PUBLIC_URL")

async def create_share_token(req: ShareTokenRequest) -> ShareTokenResponse:
    try:
        exp = int(time.time()) + req.expires_hours * 3600
        payload = {"device_id": req.device_id, "exp": exp, "type": "share"}
        token = jwt.encode(payload, _JWT_SECRET, algorithm=_ALGO)
        url = f"{_PUBLIC_URL}/?track={token}"
        
        return ShareTokenResponse(
            token=token,
            url=url,
            device_id=req.device_id,
            expires_at=datetime.utcfromtimestamp(exp).isoformat()
        )
    except Exception as e:
        logger.error(f"Error creating share token: {e}")
        raise e

