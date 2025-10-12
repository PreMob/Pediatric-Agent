from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, delete
from typing import List

from app.core.v1.db import get_db
from app.api.v1.schemas.user.user import User
from app.api.v1.schemas.user.child import Child
from app.api.v1.schemas import (
    ChildCreate,
    ChildResponse,
    ChildUpdate
)
from app.api.v1.routes.user import get_current_user
from app.core.v1.common.logger import get_logger
from app.core.v1.common.exceptions import NotFoundOrAccessException, ConflictException

# Initialize router and logger
router = APIRouter()
logger = get_logger("child_routes")

# Routes
@router.post("/", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def add_child(
    child_data: ChildCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a child under the authenticated user."""
    logger.info(f"User {current_user.id} attempting to add child: {child_data.name}")
    
    try:
        # Create new child
        new_child = Child(
            name=child_data.name,
            age=child_data.age,
            parent_id=current_user.id  # type: ignore
        )
        
        db.add(new_child)
        await db.commit()
        await db.refresh(new_child)
        
        logger.info(f"Successfully added child {new_child.name} for user {current_user.id}")
        return ChildResponse.from_orm(new_child)
        
    except IntegrityError:
        await db.rollback()
        logger.error(f"Database integrity error during child creation for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during child creation"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during child creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during child creation"
        )

@router.get("/", response_model=List[ChildResponse])
async def list_children(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all children of the authenticated user."""
    logger.info(f"Getting children list for user {current_user.id}")
    
    # Get all children for the current user
    result = await db.execute(
        select(Child).filter(Child.parent_id == current_user.id)  # type: ignore
    )
    children = result.scalars().all()
    
    logger.info(f"Found {len(children)} children for user {current_user.id}")
    return [ChildResponse.from_orm(child) for child in children]

@router.get("/{child_id}", response_model=ChildResponse)
async def get_child_details(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get single child details."""
    logger.info(f"Getting details for child ID: {child_id}")
    
    # Get child from database
    result = await db.execute(select(Child).filter(Child.id == child_id))
    child = result.scalar_one_or_none()
    
    if not child:
        logger.warning(f"Child not found: {child_id}")
        raise NotFoundOrAccessException("Child")
    
    # Check if child belongs to current user
    if child.parent_id != current_user.id:  # type: ignore
        logger.warning(f"Unauthorized access: user {current_user.id} tried to access child {child_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this child record"
        )
    
    logger.info(f"Successfully retrieved child details: {child.name}")
    return ChildResponse.from_orm(child)

@router.put("/{child_id}", response_model=ChildResponse)
async def update_child_info(
    child_id: int,
    child_update: ChildUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update child information."""
    logger.info(f"Updating child ID: {child_id}")
    
    # Get child from database
    result = await db.execute(select(Child).filter(Child.id == child_id))
    child = result.scalar_one_or_none()
    
    if not child:
        logger.warning(f"Child not found for update: {child_id}")
        raise NotFoundOrAccessException("Child")
    
    # Check if child belongs to current user
    if child.parent_id != current_user.id:  # type: ignore
        logger.warning(f"Unauthorized update: user {current_user.id} tried to update child {child_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this child record"
        )
    
    try:
        # Prepare update data
        update_data = {}
        
        if child_update.name is not None:
            update_data['name'] = child_update.name
            
        if child_update.age is not None:
            update_data['age'] = child_update.age
        
        if update_data:
            await db.execute(
                update(Child).where(Child.id == child_id).values(**update_data)
            )
        
        await db.commit()
        await db.refresh(child)
        
        logger.info(f"Successfully updated child: {child.name}")
        return ChildResponse.from_orm(child)
        
    except IntegrityError:
        await db.rollback()
        logger.error(f"Database integrity error during child update for ID: {child_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during child update"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during child update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during child update"
        )

@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_child_record(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove child record."""
    logger.info(f"Deleting child ID: {child_id}")
    
    # Get child from database
    result = await db.execute(select(Child).filter(Child.id == child_id))
    child = result.scalar_one_or_none()
    
    if not child:
        logger.warning(f"Child not found for deletion: {child_id}")
        raise NotFoundOrAccessException("Child")
    
    # Check if child belongs to current user
    if child.parent_id != current_user.id:  # type: ignore
        logger.warning(f"Unauthorized deletion: user {current_user.id} tried to delete child {child_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this child record"
        )
    
    try:
        # Delete child
        await db.execute(delete(Child).where(Child.id == child_id))
        await db.commit()
        
        logger.info(f"Successfully deleted child: {child.name}")
        return None
        
    except IntegrityError:
        await db.rollback()
        logger.error(f"Database integrity error during child deletion for ID: {child_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during child deletion"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during child deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during child deletion"
        )
