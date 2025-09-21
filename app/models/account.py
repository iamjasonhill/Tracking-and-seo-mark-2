from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Account(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    provider = Column(String, nullable=False)
    credentials = Column(JSON, nullable=False)
    owner = relationship("User", back_populates="accounts")
    sites = relationship("Site", back_populates="account")
