from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional
from app.core.v1.db import Base

# SQLAlchemy Model
class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)

    parent_id = Column(Integer, ForeignKey("users.id"))
    parent = relationship("User", back_populates="children")

# Pydantic Schemas
class ChildCreate(BaseModel):
    name: str
    age: Optional[int] = None

class ChildResponse(BaseModel):
    id: int
    name: str
    age: Optional[int] = None
    parent_id: int
    
    class Config:
        from_attributes = True

class ChildUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
