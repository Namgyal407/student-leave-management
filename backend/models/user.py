from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    year = Column(String(20))
    department = Column(String(100))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "email": self.email,
            "role": self.role, "year": self.year, "department": self.department,
            "phone": self.phone, "is_active": self.is_active,
        }
