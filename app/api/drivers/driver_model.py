from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from app.db.base_gps import BaseGPS
from datetime import datetime

class Driver(BaseGPS):
    __tablename__ = "drivers"
    
    id = Column(Integer, primary_key=True)
    traccar_driver_id = Column(Integer, unique=True, index=True)
    name = Column(String)
    unique_id = Column(String, unique=True, index=True)
    attributes = Column(JSON, nullable=True)
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


