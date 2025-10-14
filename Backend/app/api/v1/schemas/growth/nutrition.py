from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Text
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.core.v1.db import Base

# SQLAlchemy Model
class Nutrition(Base):
    __tablename__ = "nutrition_logs"

    id = Column(Integer, primary_key=True, index=True)
    meal_type = Column(String(50), nullable=False)  # breakfast, lunch, dinner, snack
    food_items = Column(Text, nullable=False)  # JSON string of food items
    calories = Column(Float, nullable=True)  # Total calories
    protein_g = Column(Float, nullable=True)  # Protein in grams
    carbs_g = Column(Float, nullable=True)  # Carbohydrates in grams
    fat_g = Column(Float, nullable=True)  # Fat in grams
    fiber_g = Column(Float, nullable=True)  # Fiber in grams
    sodium_mg = Column(Float, nullable=True)  # Sodium in milligrams
    meal_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(String(500), nullable=True)
    
    child_id = Column(Integer, ForeignKey("children.id"))
    child = relationship("Child", back_populates="nutrition_logs")  # type: ignore

# Pydantic Schemas
class FoodItem(BaseModel):
    name: str = Field(..., description="Name of the food item")
    quantity: str = Field(..., description="Quantity (e.g., '1 cup', '2 slices')")
    calories_per_serving: Optional[float] = Field(None, description="Calories per serving")

class NutritionCreate(BaseModel):
    meal_type: str = Field(..., description="Type of meal", pattern="^(breakfast|lunch|dinner|snack)$")
    food_items: List[FoodItem] = Field(..., description="List of food items consumed")
    calories: Optional[float] = Field(None, description="Total calories", ge=0, le=5000)
    protein_g: Optional[float] = Field(None, description="Protein in grams", ge=0, le=500)
    carbs_g: Optional[float] = Field(None, description="Carbohydrates in grams", ge=0, le=1000)
    fat_g: Optional[float] = Field(None, description="Fat in grams", ge=0, le=500)
    fiber_g: Optional[float] = Field(None, description="Fiber in grams", ge=0, le=100)
    sodium_mg: Optional[float] = Field(None, description="Sodium in milligrams", ge=0, le=10000)
    meal_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)

class NutritionResponse(BaseModel):
    id: int
    meal_type: str
    food_items: List[FoodItem]
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    meal_date: datetime
    notes: Optional[str] = None
    child_id: int
    
    class Config:
        from_attributes = True

class NutritionUpdate(BaseModel):
    meal_type: Optional[str] = Field(None, description="Type of meal", pattern="^(breakfast|lunch|dinner|snack)$")
    food_items: Optional[List[FoodItem]] = Field(None, description="List of food items consumed")
    calories: Optional[float] = Field(None, description="Total calories", ge=0, le=5000)
    protein_g: Optional[float] = Field(None, description="Protein in grams", ge=0, le=500)
    carbs_g: Optional[float] = Field(None, description="Carbohydrates in grams", ge=0, le=1000)
    fat_g: Optional[float] = Field(None, description="Fat in grams", ge=0, le=500)
    fiber_g: Optional[float] = Field(None, description="Fiber in grams", ge=0, le=100)
    sodium_mg: Optional[float] = Field(None, description="Sodium in milligrams", ge=0, le=10000)
    meal_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)

class DailyNutrition(BaseModel):
    """Daily nutritional summary"""
    date: str
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_fiber_g: float
    total_sodium_mg: float
    meal_count: int
    meals_by_type: dict  # {"breakfast": 1, "lunch": 1, "dinner": 1, "snack": 2}

class NutritionSummary(BaseModel):
    """Comprehensive nutritional summary"""
    total_logs: int
    date_range: str  # "Last 7 days" or specific date range
    daily_averages: dict  # {"calories": 1200, "protein_g": 45, etc.}
    recent_daily_summaries: List[DailyNutrition]
    most_common_foods: List[str]
    nutrition_goals_status: dict  # {"calories": "below_target", "protein": "adequate", etc.}
    recommendations: List[str]  # Nutritional recommendations