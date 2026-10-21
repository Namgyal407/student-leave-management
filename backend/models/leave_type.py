from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import Base


class LeaveType(Base):
    __tablename__ = "leave_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    max_days = Column(Integer, default=30)
    requires_doc = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "max_days": self.max_days, "requires_doc": self.requires_doc,
            "is_active": self.is_active,
        }
