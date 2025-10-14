from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List
from datetime import datetime, timedelta
import json
from collections import defaultdict, Counter

from app.core.v1.db import get_db
from app.core.v1.common.logger import get_logger
from app.api.v1.schemas import (
    Nutrition, 
    Child,
    FoodItem,
    NutritionCreate, 
    NutritionResponse, 
    NutritionUpdate,
    DailyNutrition,
    NutritionSummary
)
from app.api.v1.routes.user import get_current_user
from app.api.v1.schemas.user.user import User

router = APIRouter()
logger = get_logger("nutrition_routes")

async def verify_child_parent(child_id: int, current_user: User, session: AsyncSession) -> Child:
    """Verify that the child belongs to the current user (parent)"""
    result = await session.execute(
        select(Child).where(Child.id == child_id, Child.parent_id == current_user.id)
    )
    child = result.scalar_one_or_none()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or you don't have permission to access this child's nutrition data"
        )
    return child

def calculate_daily_nutrition(nutrition_logs) -> List[DailyNutrition]:
    """Calculate daily nutrition summaries from logs"""
    daily_data = defaultdict(lambda: {
        'calories': 0.0,
        'protein_g': 0.0,
        'carbs_g': 0.0,
        'fat_g': 0.0,
        'fiber_g': 0.0,
        'sodium_mg': 0.0,
        'meal_count': 0,
        'meals_by_type': defaultdict(int)
    })
    
    for log in nutrition_logs:
        date_str = log.meal_date.strftime("%Y-%m-%d")  # type: ignore
        daily = daily_data[date_str]
        
        daily['calories'] += float(log.calories or 0)  # type: ignore
        daily['protein_g'] += float(log.protein_g or 0)  # type: ignore
        daily['carbs_g'] += float(log.carbs_g or 0)  # type: ignore
        daily['fat_g'] += float(log.fat_g or 0)  # type: ignore
        daily['fiber_g'] += float(log.fiber_g or 0)  # type: ignore
        daily['sodium_mg'] += float(log.sodium_mg or 0)  # type: ignore
        daily['meal_count'] += 1  # type: ignore
        daily['meals_by_type'][log.meal_type] += 1  # type: ignore
    
    daily_summaries = []
    for date_str, data in sorted(daily_data.items()):
        daily_summaries.append(DailyNutrition(
            date=date_str,
            total_calories=round(float(data['calories']), 1),  # type: ignore
            total_protein_g=round(float(data['protein_g']), 1),  # type: ignore
            total_carbs_g=round(float(data['carbs_g']), 1),  # type: ignore
            total_fat_g=round(float(data['fat_g']), 1),  # type: ignore
            total_fiber_g=round(float(data['fiber_g']), 1),  # type: ignore
            total_sodium_mg=round(float(data['sodium_mg']), 1),  # type: ignore
            meal_count=int(data['meal_count']),  # type: ignore
            meals_by_type=dict(data['meals_by_type'])  # type: ignore
        ))
    
    return daily_summaries

def get_nutrition_recommendations(avg_nutrition: dict, child_age: int) -> List[str]:
    """Generate nutrition recommendations based on averages and child age"""
    recommendations = []
    
    # Basic age-based daily requirements (simplified)
    if child_age <= 12:  # 0-12 months
        target_calories = 800
        target_protein = 15
    elif child_age <= 24:  # 1-2 years
        target_calories = 1000
        target_protein = 20
    else:  # 2+ years
        target_calories = 1200
        target_protein = 25
    
    # Calorie recommendations
    if avg_nutrition['calories'] < target_calories * 0.8:
        recommendations.append(f"Consider increasing daily calories. Target: ~{target_calories} calories/day")
    elif avg_nutrition['calories'] > target_calories * 1.2:
        recommendations.append("Daily calorie intake seems high. Consider portion control.")
    
    # Protein recommendations
    if avg_nutrition['protein_g'] < target_protein * 0.8:
        recommendations.append(f"Increase protein intake. Target: ~{target_protein}g protein/day")
    
    # Fiber recommendations
    if avg_nutrition['fiber_g'] < 10:
        recommendations.append("Include more fruits, vegetables, and whole grains for fiber")
    
    # Sodium recommendations
    if avg_nutrition['sodium_mg'] > 1500:
        recommendations.append("Reduce sodium intake. Limit processed foods.")
    
    if not recommendations:
        recommendations.append("Nutritional intake looks well-balanced!")
    
    return recommendations

@router.post("/", response_model=NutritionResponse, status_code=status.HTTP_201_CREATED)
async def add_meal_log(
    child_id: int,
    nutrition_data: NutritionCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new meal log for a child"""
    
    # Verify child belongs to current user
    child = await verify_child_parent(child_id, current_user, session)
    
    # Convert food_items to JSON string for storage
    food_items_json = json.dumps([item.dict() for item in nutrition_data.food_items])
    
    # Create nutrition log
    nutrition_log = Nutrition(
        child_id=child.id,
        meal_type=nutrition_data.meal_type,
        food_items=food_items_json,
        calories=nutrition_data.calories,
        protein_g=nutrition_data.protein_g,
        carbs_g=nutrition_data.carbs_g,
        fat_g=nutrition_data.fat_g,
        fiber_g=nutrition_data.fiber_g,
        sodium_mg=nutrition_data.sodium_mg,
        meal_date=nutrition_data.meal_date or datetime.utcnow(),
        notes=nutrition_data.notes
    )
    
    session.add(nutrition_log)
    await session.commit()
    await session.refresh(nutrition_log)
    
    # Parse food_items back for response
    parsed_food_items = [FoodItem(**item) for item in json.loads(nutrition_log.food_items)]  # type: ignore
    
    response = NutritionResponse(
        id=nutrition_log.id,  # type: ignore
        meal_type=nutrition_log.meal_type,  # type: ignore
        food_items=parsed_food_items,
        calories=nutrition_log.calories,  # type: ignore
        protein_g=nutrition_log.protein_g,  # type: ignore
        carbs_g=nutrition_log.carbs_g,  # type: ignore
        fat_g=nutrition_log.fat_g,  # type: ignore
        fiber_g=nutrition_log.fiber_g,  # type: ignore
        sodium_mg=nutrition_log.sodium_mg,  # type: ignore
        meal_date=nutrition_log.meal_date,  # type: ignore
        notes=nutrition_log.notes,  # type: ignore
        child_id=nutrition_log.child_id  # type: ignore
    )
    
    return response

@router.get("/{child_id}", response_model=List[NutritionResponse])
async def get_nutrition_history(
    child_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete nutrition history for a child"""
    
    # Verify child belongs to current user
    await verify_child_parent(child_id, current_user, session)
    
    # Get all nutrition logs for the child, ordered by date (newest first)
    result = await session.execute(
        select(Nutrition)
        .where(Nutrition.child_id == child_id)
        .order_by(desc(Nutrition.meal_date))
    )
    nutrition_logs = result.scalars().all()
    
    # Parse food_items for each log
    response_logs = []
    for log in nutrition_logs:
        parsed_food_items = [FoodItem(**item) for item in json.loads(log.food_items)]  # type: ignore
        
        response_logs.append(NutritionResponse(
            id=log.id,  # type: ignore
            meal_type=log.meal_type,  # type: ignore
            food_items=parsed_food_items,
            calories=log.calories,  # type: ignore
            protein_g=log.protein_g,  # type: ignore
            carbs_g=log.carbs_g,  # type: ignore
            fat_g=log.fat_g,  # type: ignore
            fiber_g=log.fiber_g,  # type: ignore
            sodium_mg=log.sodium_mg,  # type: ignore
            meal_date=log.meal_date,  # type: ignore
            notes=log.notes,  # type: ignore
            child_id=log.child_id  # type: ignore
        ))
    
    return response_logs

@router.get("/summary/{child_id}", response_model=NutritionSummary)
async def get_nutrition_summary(
    child_id: int,
    days: int = 7,  # Default to last 7 days
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get nutritional summary report for a child"""
    
    # Verify child belongs to current user
    child = await verify_child_parent(child_id, current_user, session)
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get nutrition logs for the specified period
    result = await session.execute(
        select(Nutrition)
        .where(
            Nutrition.child_id == child_id,
            Nutrition.meal_date >= start_date,
            Nutrition.meal_date <= end_date
        )
        .order_by(Nutrition.meal_date)
    )
    nutrition_logs = result.scalars().all()
    
    total_logs = len(nutrition_logs)
    
    if total_logs == 0:
        return NutritionSummary(
            total_logs=0,
            date_range=f"Last {days} days",
            daily_averages={},
            recent_daily_summaries=[],
            most_common_foods=[],
            nutrition_goals_status={},
            recommendations=["No nutrition data available. Start logging meals!"]
        )
    
    # Calculate daily summaries
    daily_summaries = calculate_daily_nutrition(nutrition_logs)
    
    # Calculate averages
    total_days = len(daily_summaries) if daily_summaries else 1
    total_calories = sum(float(log.calories or 0) for log in nutrition_logs)  # type: ignore
    total_protein = sum(float(log.protein_g or 0) for log in nutrition_logs)  # type: ignore
    total_carbs = sum(float(log.carbs_g or 0) for log in nutrition_logs)  # type: ignore
    total_fat = sum(float(log.fat_g or 0) for log in nutrition_logs)  # type: ignore
    total_fiber = sum(float(log.fiber_g or 0) for log in nutrition_logs)  # type: ignore
    total_sodium = sum(float(log.sodium_mg or 0) for log in nutrition_logs)  # type: ignore
    
    daily_averages = {
        "calories": round(total_calories / total_days, 1),
        "protein_g": round(total_protein / total_days, 1),
        "carbs_g": round(total_carbs / total_days, 1),
        "fat_g": round(total_fat / total_days, 1),
        "fiber_g": round(total_fiber / total_days, 1),
        "sodium_mg": round(total_sodium / total_days, 1)
    }
    
    # Find most common foods
    all_foods = []
    for log in nutrition_logs:
        try:
            food_items = json.loads(log.food_items)  # type: ignore
            for item in food_items:
                all_foods.append(item['name'])
        except:
            continue
    
    food_counter = Counter(all_foods)
    most_common_foods = [food for food, count in food_counter.most_common(5)]
    
    # Generate recommendations
    child_age = int(child.age or 12)  # type: ignore
    recommendations = get_nutrition_recommendations(daily_averages, child_age)
    
    # Nutrition goals status (simplified)
    nutrition_goals_status = {
        "calories": "adequate" if 800 <= daily_averages["calories"] <= 1500 else "needs_attention",
        "protein": "adequate" if daily_averages["protein_g"] >= 15 else "low",
        "fiber": "adequate" if daily_averages["fiber_g"] >= 10 else "low",
        "sodium": "good" if daily_averages["sodium_mg"] <= 1500 else "high"
    }
    
    return NutritionSummary(
        total_logs=total_logs,
        date_range=f"Last {days} days",
        daily_averages=daily_averages,
        recent_daily_summaries=daily_summaries[-7:],  # Last 7 days
        most_common_foods=most_common_foods,
        nutrition_goals_status=nutrition_goals_status,
        recommendations=recommendations
    )