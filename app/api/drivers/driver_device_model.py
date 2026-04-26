from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.base_gps import BaseGPS

class DriverDeviceLink(BaseGPS):
    __tablename__ = "driver_device_link"
    
    id = Column(Integer, primary_key=True)
    driver_unique_id = Column(String, ForeignKey("drivers.unique_id", ondelete="CASCADE"), index=True)
    device_unique_id = Column(String, ForeignKey("devices.unique_id", ondelete="CASCADE"), index=True)
