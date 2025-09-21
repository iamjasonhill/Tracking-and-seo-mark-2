from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Site(Base):
    __tablename__ = 'sites'
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'))
    site_url = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    account = relationship("Account", back_populates="sites")
    search_data = relationship("SearchData", back_populates="site")
    sync_jobs = relationship("SyncJob", back_populates="site")
