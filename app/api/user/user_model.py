from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Integer, Column
from sqlalchemy.orm import relationship
from app.db.base_main import BaseMain
from typing import Optional

class User(BaseMain):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    password = Column(String)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    alive = Column(Boolean, default=True)
    
    enterprises = relationship(
        "Enterprise",
        secondary="enterprise_user_link",
        back_populates="users",
        lazy="selectin"
    )

    @property
    def enterprise_id(self) -> Optional[int]:
        if self.enterprises:
            return self.enterprises[0].id
        return None

    @property
    def enterprise_name(self) -> str:
        if self.enterprises:
            return self.enterprises[0].fullname
        return "N/A"
