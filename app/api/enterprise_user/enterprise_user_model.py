from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Column
from app.db.base_main import BaseMain

class EnterpriseUserLink(BaseMain):
    __tablename__ = "enterprise_user_link"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    enterprise_id = Column(ForeignKey("enterprise.id"))
    user_id = Column(ForeignKey("user.id"))
    role = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)