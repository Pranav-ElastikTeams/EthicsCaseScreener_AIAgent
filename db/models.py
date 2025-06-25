from sqlalchemy import Column, Integer, String, Text, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Complaint(Base):
    __tablename__ = 'complaints'
    complaint_id = Column(String(20), primary_key=True)
    date = Column(Date)
    complainant = Column(String(100))
    complainant_email = Column(String(100))
    complaint_type = Column(String(100))
    subject = Column(String(150))
    details_summary = Column(Text)
    evidence_provided = Column(String(150))
    status = Column(String(50))
    assigned_officer = Column(String(100))
    staff_role = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
