from fastapi import FastAPI
from .api.v1 import health

app = FastAPI(title="Pediatric Growth & Nutrition Agent API", version="1.0")

app.include_router(health.router, prefix="/api/v1/health", tags=["health"])

@app.get("/")
def root():
    return {"message": "Pediatric Growth & Nutrition Agent Backend is running 🚀"}
