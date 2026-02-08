from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

from api import auth, slots, webhooks

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Calendar Sync Backend...")
    print(f"📁 Database: {os.getenv('DATABASE_URL')}")
    print(f"🔗 Webhook URL: {os.getenv('WEBHOOK_BASE_URL')}")
    yield
    print("👋 Shutting down...")

app = FastAPI(
    title="Calendar Sync Backend",
    description="Two-way Google Calendar synchronization",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, tags=["Authentication"])
app.include_router(slots.router, tags=["Slots"])
app.include_router(webhooks.router, tags=["Webhooks"])

@app.get("/")
def root():
    return {
        "message": "Calendar Sync Backend API",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )