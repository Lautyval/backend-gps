from sqlalchemy import String, DateTime, Float, Integer, ForeignKey, Boolean, Column
from app.db.base_gps import BaseGPS
from datetime import datetime

class AlertRule(BaseGPS):
    __tablename__ = "alert_rule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    device_id = Column(Integer, nullable=True)  # None = all devices
    condition = Column(String)  # 'speed' | 'stopped' | 'offline'
    threshold = Column(Float, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
