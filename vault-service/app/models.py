from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime
from sqlalchemy.sql import func


Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    owner_email = Column(String, nullable=False)

    filename = Column(String, nullable=False)

    s3_key = Column(String, nullable=False)

    status = Column(String, default="Pending")

    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String)
    action = Column(String)
    filename = Column(String)
    created_at = Column(DateTime, server_default=func.now())