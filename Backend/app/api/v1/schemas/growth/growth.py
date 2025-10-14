from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.core.v1.db import Base

# SQLAlchemy Model
class Growth(Base):
    __tablename__ = "growth_logs"

    id = Column(Integer, primary_key=True, index=True)
    height_cm = Column(Float, nullable=True)  # Height in centimeters
    weight_kg = Column(Float, nullable=True)  # Weight in kilograms
    head_circumference_cm = Column(Float, nullable=True)  # Head circumference in centimeters
    measurement_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(String(500), nullable=True)
    
    child_id = Column(Integer, ForeignKey("children.id"))
    child = relationship("Child", back_populates="growth_logs")  # type: ignore

# Pydantic Schemas
class GrowthCreate(BaseModel):
    height_cm: Optional[float] = Field(None, description="Height in centimeters", ge=0, le=300)
    weight_kg: Optional[float] = Field(None, description="Weight in kilograms", ge=0, le=200)
    head_circumference_cm: Optional[float] = Field(None, description="Head circumference in centimeters", ge=0, le=100)
    measurement_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)

class GrowthResponse(BaseModel):
    id: int
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    head_circumference_cm: Optional[float] = None
    measurement_date: datetime
    notes: Optional[str] = None
    child_id: int
    
    class Config:
        from_attributes = True

class GrowthUpdate(BaseModel):
    height_cm: Optional[float] = Field(None, description="Height in centimeters", ge=0, le=300)
    weight_kg: Optional[float] = Field(None, description="Weight in kilograms", ge=0, le=200)
    head_circumference_cm: Optional[float] = Field(None, description="Head circumference in centimeters", ge=0, le=100)
    measurement_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)

class GrowthStats(BaseModel):
    """Growth statistics and analysis"""
    total_measurements: int
    latest_height_cm: Optional[float] = None
    latest_weight_kg: Optional[float] = None
    latest_head_circumference_cm: Optional[float] = None
    height_trend: Optional[str] = None  # "increasing", "stable", "decreasing"
    weight_trend: Optional[str] = None
    head_circumference_trend: Optional[str] = None
    height_percentile: Optional[float] = None  # Based on WHO growth charts
    weight_percentile: Optional[float] = None
    head_circumference_percentile: Optional[float] = None