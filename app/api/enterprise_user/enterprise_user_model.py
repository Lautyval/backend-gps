from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Float, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_main import BaseMain
from app.db.base_gps import BaseGPS

class EnterpriseUserLink(BaseMain):
    __tablename__ = "enterprise_user_link"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("enterprise.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    role: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

# Tenant Models
class POI(BaseGPS):
    __tablename__ = "poi"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    color: Mapped[str] = mapped_column(String)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class MaintenanceRecord(BaseGPS):
    __tablename__ = "maintenance_record"

    device_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    serviceName: Mapped[str] = mapped_column(String)
    intervalDays: Mapped[int] = mapped_column(Integer)
    lastServiceDate: Mapped[str] = mapped_column(String) # "YYYY-MM-DD"
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AlertRule(BaseGPS):
    __tablename__ = "alert_rule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    device_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = all devices
    condition: Mapped[str] = mapped_column(String)  # 'speed' | 'stopped' | 'offline'
    threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
