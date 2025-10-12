from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os

from app.core.v1.db import get_db
from app.api.v1.schemas.user.user import User
from app.api.v1.schemas import (
    UserRegister,
    UserLogin, 
    UserResponse,
    UserUpdate,
    Token
)
from app.core.v1.common.logger import get_logger
from app.core.v1.common.exceptions import NotFoundOrAccessException, ConflictException

# Initialize router and logger
router = APIRouter()
logger = get_logger("user_routes")

# Security configurations
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user

# Routes
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    logger.info(f"Attempting to register user with email: {user_data.email}")
    
    try:
        # Check if user already exists
        result = await db.execute(select(User).filter(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.warning(f"User registration failed: email {user_data.email} already exists")
            raise ConflictException("User with this email")
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create new user
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"Successfully registered user: {new_user.email}")
        return UserResponse.from_orm(new_user)
        
    except IntegrityError:
        await db.rollback()
        logger.error(f"Database integrity error during user registration for email: {user_data.email}")
        raise ConflictException("User with this email")
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )

@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return access token."""
    logger.info(f"Login attempt for email: {user_credentials.email}")
    
    # Get user from database
    result = await db.execute(select(User).filter(User.email == user_credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):  # type: ignore
        logger.warning(f"Failed login attempt for email: {user_credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    logger.info(f"Successfully logged in user: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user profile by ID."""
    logger.info(f"Getting profile for user ID: {user_id}")
    
    # Check if user is accessing their own profile or has admin rights
    if current_user.id != user_id:  # type: ignore
        logger.warning(f"Unauthorized access attempt: user {current_user.id} tried to access user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user profile"
        )
    
    # Get user from database
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise NotFoundOrAccessException("User")
    
    logger.info(f"Successfully retrieved profile for user: {user.email}")
    return UserResponse.from_orm(user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_info(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user information."""
    logger.info(f"Updating user ID: {user_id}")
    
    # Check if user is updating their own profile
    if current_user.id != user_id:  # type: ignore
        logger.warning(f"Unauthorized update attempt: user {current_user.id} tried to update user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user profile"
        )
    
    # Get user from database
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"User not found for update: {user_id}")
        raise NotFoundOrAccessException("User")
    
    try:
        # Prepare update data
        update_data = {}
        
        if user_update.email is not None:
            # Check if new email already exists
            email_result = await db.execute(
                select(User).filter(User.email == user_update.email, User.id != user_id)
            )
            if email_result.scalar_one_or_none():
                logger.warning(f"Email update failed: {user_update.email} already exists")
                raise ConflictException("User with this email")
            update_data['email'] = user_update.email
            
        if user_update.full_name is not None:
            update_data['full_name'] = user_update.full_name
        
        if update_data:
            await db.execute(
                update(User).where(User.id == user_id).values(**update_data)
            )
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Successfully updated user: {user.email}")
        return UserResponse.from_orm(user)
        
    except IntegrityError:
        await db.rollback()
        logger.error(f"Database integrity error during user update for ID: {user_id}")
        raise ConflictException("User with this email")
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during user update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during update"
        )