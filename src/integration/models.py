from sqlalchemy import Column, String, Boolean, Integer, JSON, DateTime
from .database import Base
from datetime import datetime

class WorkflowStructure(Base):
    __tablename__ = "workflow_structures"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    status = Column(String)
    fields = Column(JSON)
    api_config = Column(JSON)
    category = Column(String)
    version = Column(Integer)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
