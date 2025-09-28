# core/v1/models/child.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Backend.app.core.v1.db import Base

class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)

    parent_id = Column(Integer, ForeignKey("users.id"))
    parent = relationship("User", back_populates="children")
