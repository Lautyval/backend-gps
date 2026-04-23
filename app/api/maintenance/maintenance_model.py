from sqlalchemy import Column, String, DateTime, Float, Integer
from app.db.base_gps import BaseGPS
from datetime import datetime

class MaintenanceRecord(BaseGPS):
    __tablename__ = "maintenance_record"

    device_id = Column(Integer, primary_key=True)
    serviceName = Column(String)
    intervalDays = Column(Integer)
    intervalKm = Column(Integer, default=10000)
    lastServiceDate = Column(String) # "YYYY-MM-DD"
    lastServiceKm = Column(Float, default=0)
    alertStrategy = Column(String, default='both') # 'days', 'km', 'both'
    notes = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)