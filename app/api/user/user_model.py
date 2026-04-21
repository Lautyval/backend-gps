from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_main import BaseMain

if TYPE_CHECKING:
    from app.api.enterprise.enterprise_model import Enterprise
    from app.api.enterprise_user.enterprise_user_model import EnterpriseUserLink

class User(BaseMain):
    __tablename__ = "user"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    password: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    alive: Mapped[bool] = mapped_column(Boolean, default=True)
    
    enterprises: Mapped[List["Enterprise"]] = relationship(
        "Enterprise",
        secondary="enterprise_user_link",
        back_populates="users",
        lazy="selectin"
    )
