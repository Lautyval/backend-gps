from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.db.base_gps import BaseGPS
from datetime import datetime

class Geofence(BaseGPS):
    __tablename__ = "geofences"
    
    id = Column(Integer, primary_key=True)
    traccar_geofence_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
