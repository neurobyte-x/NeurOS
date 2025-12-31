"""
Routes package initialization.

WHY: Clean route organization by domain.
Each route module handles a specific resource.
"""

from fastapi import APIRouter

from routes.entries import router as entries_router
from routes.patterns import router as patterns_router
from routes.recall import router as recall_router
from routes.analytics import router as analytics_router
from routes.ai import router as ai_router
from routes.recommendations import router as recommendations_router
from routes.plans import router as plans_router

# Main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(entries_router, prefix="/entries", tags=["entries"])
api_router.include_router(patterns_router, prefix="/patterns", tags=["patterns"])
api_router.include_router(recall_router, prefix="/recall", tags=["recall"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(ai_router)
api_router.include_router(recommendations_router)
api_router.include_router(plans_router)
