"""
Thinking OS - Main FastAPI Application

A personal knowledge system that captures thinking patterns,
not just solutions. Designed for daily use over years.

PHILOSOPHY:
- Reflection before persistence
- Patterns over notes
- Past struggles as teachers
- Data-driven improvement

Author: Your name
Created: 2026
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from config import settings
from database import init_db
from routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    WHY: Initialize database on startup.
    Future: Add cleanup, background tasks.
    """
    print("🧠 Initializing Thinking OS...")
    init_db()
    print("✅ Database initialized")
    print(f"📊 Running in {'DEBUG' if settings.DEBUG else 'PRODUCTION'} mode")
    
    yield
    
    print("👋 Thinking OS shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## Thinking OS - Personal Learning Intelligence System
    
    Convert daily problem-solving into reusable thinking patterns.
    
    ### Core Concepts
    
    - **Entries**: Learning moments (problems, bugs, experiments)
    - **Reflections**: Mandatory thinking capture (why stuck, what triggered insight)
    - **Patterns**: Reusable thinking patterns in your own words
    - **Recall**: Intelligence layer surfacing relevant history
    
    ### Philosophy
    
    No reflection → No persistence.
    This system captures HOW you learn, not just WHAT you learned.
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/")
async def root():
    """Welcome endpoint with quick start guide."""
    return {
        "message": "🧠 Welcome to Thinking OS",
        "description": "A personal knowledge system for capturing thinking patterns",
        "quick_start": {
            "1_create_entry": "POST /api/v1/entries - Create a learning entry",
            "2_add_reflection": "POST /api/v1/entries/{id}/reflection - Add mandatory reflection",
            "3_get_recall": "POST /api/v1/recall/context - Get relevant history before new work",
            "4_browse_patterns": "GET /api/v1/patterns - View your pattern vocabulary",
            "5_track_progress": "GET /api/v1/analytics/insights - See progress insights",
        },
        "docs": "/docs",
        "redoc": "/redoc",
    }


frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    @app.get("/app/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend SPA."""
        return FileResponse(os.path.join(frontend_path, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
