from fastapi import FastAPI
import asyncio
from app.api.v1.routes import health, user, child
from app.core.v1.db import mysql_engine, Base
from app.api.v1.schemas.user.user import User
from app.api.v1.schemas.user.child import Child
from app.api.v1.middlewares.error_handler import ErrorHandlerMiddleware

app = FastAPI(title="Pediatric Growth & Nutrition Agent API", version="1.0")

# Add middleware
app.add_middleware(ErrorHandlerMiddleware)

# Include routers
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(user.router, prefix="/api/v1/users", tags=["users"])
app.include_router(child.router, prefix="/api/v1/children", tags=["children"])

@app.get("/")
def root():
    return {"message": "Pediatric Growth & Nutrition Agent Backend is running "}

async def init_db():
    try:
        async with mysql_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Please check your .env file and ensure MySQL is running")
        return False
    return True
        
if __name__ == "__main__":
    asyncio.run(init_db())