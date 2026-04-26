from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.db.base_gps import BaseGPS
from datetime import datetime

class ShareLink(BaseGPS):
    __tablename__ = "share_links"
    
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, index=True)
    device_id = Column(Integer)
    expires_at = Column(DateTime)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
