from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_main import BaseMain

if TYPE_CHECKING:
    from app.api.user.user_model import User

class Enterprise(BaseMain):
    __tablename__ = "enterprise"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    fullname: Mapped[str] = mapped_column(String)
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="enterprise_user_link",
        back_populates="enterprises",
        lazy="selectin"
    )
