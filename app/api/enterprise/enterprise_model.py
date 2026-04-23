from datetime import datetime
from sqlalchemy import String, DateTime, Float, Integer, Column, Boolean
from sqlalchemy.orm import relationship
from app.db.base_main import BaseMain

class Enterprise(BaseMain):
    __tablename__ = "enterprise"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, index=True)
    fullname = Column(String)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship(
        "User",
        secondary="enterprise_user_link",
        back_populates="enterprises",
        lazy="selectin"
    )

