from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List
from datetime import datetime, timedelta

from app.core.v1.db import get_db
from app.core.v1.common.logger import get_logger
from app.api.v1.schemas import (
    Growth, 
    Child,
    GrowthCreate, 
    GrowthResponse, 
    GrowthUpdate,
    GrowthStats
)
from app.api.v1.routes.user import get_current_user
from app.api.v1.schemas.user.user import User

router = APIRouter()
logger = get_logger("growth_routes")

async def verify_child_parent(child_id: int, current_user: User, session: AsyncSession) -> Child:
    """Verify that the child belongs to the current user (parent)"""
    result = await session.execute(
        select(Child).where(Child.id == child_id, Child.parent_id == current_user.id)
    )
    child = result.scalar_one_or_none()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or you don't have permission to access this child's growth data"
        )
    return child

def calculate_trend(measurements: List[float]) -> str:
    """Calculate trend from measurements (simple linear trend)"""
    if len(measurements) < 2:
        return "insufficient_data"
    
    # Calculate simple trend over recent measurements
    recent_measurements = measurements[-3:] if len(measurements) >= 3 else measurements
    if len(recent_measurements) < 2:
        return "stable"
    
    trend_sum = sum(recent_measurements[i+1] - recent_measurements[i] for i in range(len(recent_measurements)-1))
    avg_change = trend_sum / (len(recent_measurements) - 1)
    
    if avg_change > 0.5:  # Threshold for significant increase
        return "increasing"
    elif avg_change < -0.5:  # Threshold for significant decrease
        return "decreasing"
    else:
        return "stable"

def calculate_percentile(measurement: float, measurement_type: str, age_months: int) -> float:
    """
    Calculate percentile based on WHO growth standards
    This is a simplified mock calculation - in production, use actual WHO growth charts
    """
    # Mock percentile calculation - replace with actual WHO growth chart data
    percentiles = {
        "height": {
            12: {"mean": 75.0, "std": 3.0},    # 12 months
            24: {"mean": 86.0, "std": 3.5},    # 24 months
            36: {"mean": 95.0, "std": 4.0},    # 36 months
        },
        "weight": {
            12: {"mean": 9.5, "std": 1.0},
            24: {"mean": 12.0, "std": 1.2},
            36: {"mean": 14.0, "std": 1.5},
        },
        "head_circumference": {
            12: {"mean": 46.5, "std": 1.5},
            24: {"mean": 48.0, "std": 1.5},
            36: {"mean": 49.0, "std": 1.5},
        }
    }
    
    # Find closest age group
    closest_age = min(percentiles[measurement_type].keys(), key=lambda x: abs(x - age_months))
    stats = percentiles[measurement_type][closest_age]
    
    # Calculate z-score and approximate percentile
    z_score = (measurement - stats["mean"]) / stats["std"]
    # Simplified percentile approximation
    percentile = max(0, min(100, 50 + z_score * 34.13))  # Very rough approximation
    
    return round(percentile, 1)

@router.post("/", response_model=GrowthResponse, status_code=status.HTTP_201_CREATED)
async def add_growth_log(
    child_id: int,
    growth_data: GrowthCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new growth measurement for a child"""
    
    # Verify child belongs to current user
    child = await verify_child_parent(child_id, current_user, session)
    
    # Create growth log
    growth_log = Growth(
        child_id=child.id,
        height_cm=growth_data.height_cm,
        weight_kg=growth_data.weight_kg,
        head_circumference_cm=growth_data.head_circumference_cm,
        measurement_date=growth_data.measurement_date or datetime.utcnow(),
        notes=growth_data.notes
    )
    
    session.add(growth_log)
    await session.commit()
    await session.refresh(growth_log)
    
    return growth_log

@router.get("/{child_id}", response_model=List[GrowthResponse])
async def get_child_growth_history(
    child_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete growth history for a child"""
    
    # Verify child belongs to current user
    await verify_child_parent(child_id, current_user, session)
    
    # Get all growth logs for the child, ordered by date (newest first)
    result = await session.execute(
        select(Growth)
        .where(Growth.child_id == child_id)
        .order_by(desc(Growth.measurement_date))
    )
    growth_logs = result.scalars().all()
    
    return growth_logs

@router.get("/stats/{child_id}", response_model=GrowthStats)
async def get_growth_analysis(
    child_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get growth analysis including percentiles and trends for a child"""
    
    # Verify child belongs to current user
    child = await verify_child_parent(child_id, current_user, session)
    
    # Get all growth logs for analysis
    result = await session.execute(
        select(Growth)
        .where(Growth.child_id == child_id)
        .order_by(Growth.measurement_date)
    )
    growth_logs = result.scalars().all()
    
    # Count total measurements
    total_measurements = len(growth_logs)
    
    if total_measurements == 0:
        return GrowthStats(
            total_measurements=0,
            height_trend="no_data",
            weight_trend="no_data", 
            head_circumference_trend="no_data"
        )
    
    # Get latest measurements
    latest_log = growth_logs[-1]
    latest_height = latest_log.height_cm
    latest_weight = latest_log.weight_kg
    latest_head_circumference = latest_log.head_circumference_cm
    
    # Calculate trends
    heights = [float(log.height_cm) for log in growth_logs if log.height_cm is not None]  # type: ignore
    weights = [float(log.weight_kg) for log in growth_logs if log.weight_kg is not None]  # type: ignore
    head_circumferences = [float(log.head_circumference_cm) for log in growth_logs if log.head_circumference_cm is not None]  # type: ignore
    
    height_trend = calculate_trend(heights) if heights else "no_data"
    weight_trend = calculate_trend(weights) if weights else "no_data"
    head_circumference_trend = calculate_trend(head_circumferences) if head_circumferences else "no_data"
    
    # Calculate percentiles (mock implementation)
    # In production, use actual WHO growth charts and child's exact age
    child_age_months = int(child.age or 12)  # type: ignore
    
    height_percentile = None
    weight_percentile = None
    head_circumference_percentile = None
    
    if latest_height is not None and child_age_months <= 36:
        height_percentile = calculate_percentile(float(latest_height), "height", child_age_months)  # type: ignore
    
    if latest_weight is not None and child_age_months <= 36:
        weight_percentile = calculate_percentile(float(latest_weight), "weight", child_age_months)  # type: ignore
    
    if latest_head_circumference is not None and child_age_months <= 36:
        head_circumference_percentile = calculate_percentile(float(latest_head_circumference), "head_circumference", child_age_months)  # type: ignore
    
    return GrowthStats(
        total_measurements=total_measurements,
        latest_height_cm=latest_height,  # type: ignore
        latest_weight_kg=latest_weight,  # type: ignore
        latest_head_circumference_cm=latest_head_circumference,  # type: ignore
        height_trend=height_trend,
        weight_trend=weight_trend,
        head_circumference_trend=head_circumference_trend,
        height_percentile=height_percentile,
        weight_percentile=weight_percentile,
        head_circumference_percentile=head_circumference_percentile
    )