from sqlalchemy import Column, BigInteger, Integer, String, Date, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class SearchData(Base):
    __tablename__ = 'search_data'
    id = Column(BigInteger, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey('sites.id'))
    provider = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    dimension = Column(String, nullable=False)
    key = Column(String, nullable=False)
    clicks = Column(Integer)
    impressions = Column(Integer)
    ctr = Column(Float)
    position = Column(Float)
    site = relationship("Site", back_populates="search_data")

    __table_args__ = (UniqueConstraint('site_id', 'provider', 'date', 'dimension', 'key', name='_site_provider_date_dimension_key_uc'),)
