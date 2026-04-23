from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.base_gps import BaseGPS
from datetime import datetime

class Device(BaseGPS):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True)
    traccar_device_id = Column(Integer, unique=True, index=True)
    name = Column(String)
    unique_id = Column(String, unique=True, index=True) # IMEI / ID
    created_at = Column(DateTime, default=datetime.utcnow)
