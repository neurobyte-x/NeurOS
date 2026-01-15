"""
NeurOS 2.0 API v1 Router
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, entries, patterns, reviews, decay, standup, analytics, graph

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(entries.router)
api_router.include_router(patterns.router)
api_router.include_router(reviews.router)
api_router.include_router(decay.router)
api_router.include_router(standup.router)
api_router.include_router(analytics.router)
api_router.include_router(graph.router)
