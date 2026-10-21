from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import Base


class LeaveApplication(Base):
    __tablename__ = "leave_applications"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False)
    reason = Column(Text, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default="pending")
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewer_comment = Column(Text)
    document_url = Column(String(255))
    submitted_at = Column(DateTime, server_default=func.now())
    reviewed_at = Column(DateTime)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id, "student_id": self.student_id,
            "leave_type_id": self.leave_type_id, "reason": self.reason,
            "start_date": str(self.start_date), "end_date": str(self.end_date),
            "status": self.status, "reviewed_by": self.reviewed_by,
            "reviewer_comment": self.reviewer_comment, "document_url": self.document_url,
            "submitted_at": str(self.submitted_at) if self.submitted_at else None,
            "reviewed_at": str(self.reviewed_at) if self.reviewed_at else None,
        }
