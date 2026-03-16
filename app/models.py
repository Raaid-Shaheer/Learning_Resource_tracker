from sqlalchemy import Column, Integer, String, Text
from .database import Base

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    link = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text)