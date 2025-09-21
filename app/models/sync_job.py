from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class SyncJob(Base):
    __tablename__ = 'sync_jobs'
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey('sites.id'))
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    status = Column(String)
    error = Column(Text)
    site = relationship("Site", back_populates="sync_jobs")
