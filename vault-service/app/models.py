from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    owner_email = Column(String, nullable=False)

    filename = Column(String, nullable=False)

    s3_key = Column(String, nullable=False)

    status = Column(String, default="Pending")

    uploaded_at = Column(DateTime, default=datetime.utcnow)