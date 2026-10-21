from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(30), default="info")
    related_leave_id = Column(Integer, ForeignKey("leave_applications.id"))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "title": self.title,
            "message": self.message, "type": self.type,
            "related_leave_id": self.related_leave_id, "is_read": self.is_read,
            "created_at": str(self.created_at) if self.created_at else None,
        }
