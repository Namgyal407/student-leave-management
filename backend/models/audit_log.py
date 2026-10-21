from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    ip_address = Column(String(45))
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "action": self.action,
            "entity_type": self.entity_type, "entity_id": self.entity_id,
            "old_value": self.old_value, "new_value": self.new_value,
            "ip_address": self.ip_address,
            "created_at": str(self.created_at) if self.created_at else None,
        }
