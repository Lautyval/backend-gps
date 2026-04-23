from sqlalchemy import String, DateTime, Float, Column
from app.db.base_gps import BaseGPS
from datetime import datetime

class POI(BaseGPS):
    __tablename__ = "poi"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    category = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    color = Column(String)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
