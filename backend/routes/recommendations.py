"""
Recommendation routes for Thinking OS.

WHY: Personalized recommendations are key for beginners/intermediates.
These endpoints power the recommendation system - generating, viewing,
and providing feedback on AI suggestions.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models.recommendation import (
    Recommendation, RecommendationType, 
    RecommendationPriority, RecommendationDomain
)
from schemas.recommendation import (
    GenerateRecommendationsRequest,
    RecommendationResponse,
    RecommendationSummary,
    RecommendationsListResponse,
    RecommendationFeedback,
    RecommendationUpdate,
    QuickRecommendation,
    SkillGapAnalysis,
    RecommendationDashboard
)
from services.recommendation_service import get_recommendation_service


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/generate", response_model=List[RecommendationResponse])
async def generate_recommendations(
    request: GenerateRecommendationsRequest,
    db: Session = Depends(get_db)
):
    """
    Generate personalized recommendations based on learning history.
    
    WHY: AI analyzes your entries, patterns, and progress to suggest
    what you should learn/practice next.
    
    Example: If you've been struggling with DP, it might recommend:
    - Specific DP problems at your level
    - Resources explaining the patterns you're missing
    - Revision of related concepts
    """
    service = get_recommendation_service()
    
    try:
        # Convert domains enum list to string list
        domains = [d.value for d in request.domains] if request.domains else None
        
        recommendations = service.generate_recommendations(
            db=db,
            domains=domains,
            count=request.count,
            current_focus=request.current_focus,
            difficulty_preference=request.difficulty_preference
        )
        
        # Fetch the created recommendations from DB
        recent_recs = db.query(Recommendation).order_by(
            Recommendation.created_at.desc()
        ).limit(request.count).all()
        
        return recent_recs
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.get("/quick", response_model=QuickRecommendation)
async def get_quick_recommendation(
    minutes: int = 30,
    domain: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get ONE quick recommendation for right now.
    
    WHY: "I have 30 minutes. What should I do?"
    This endpoint answers that question instantly.
    """
    service = get_recommendation_service()
    
    try:
        result = service.get_quick_recommendation(
            db=db,
            available_minutes=minutes,
            domain=domain
        )
        return QuickRecommendation(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/skill-gaps", response_model=List[SkillGapAnalysis])
async def analyze_skill_gaps(db: Session = Depends(get_db)):
    """
    Analyze your skill gaps across domains.
    
    WHY: Understand WHERE you need to improve before deciding WHAT to learn.
    Returns analysis of your strengths, weaknesses, and suggested focus.
    """
    service = get_recommendation_service()
    
    try:
        gaps = service.analyze_skill_gaps(db)
        return [SkillGapAnalysis(**g) for g in gaps]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/dashboard", response_model=RecommendationDashboard)
async def get_recommendation_dashboard(db: Session = Depends(get_db)):
    """
    Get dashboard data for recommendations section.
    
    Returns active recommendations, skill gaps, and daily suggestion.
    """
    service = get_recommendation_service()
    
    # Get active (non-completed, non-dismissed) recommendations
    active_recs = db.query(Recommendation).filter(
        Recommendation.is_completed == False,
        Recommendation.is_dismissed == False
    ).order_by(
        Recommendation.priority.desc(),
        Recommendation.created_at.desc()
    ).limit(10).all()
    
    # Get skill gaps
    try:
        skill_gaps = service.analyze_skill_gaps(db)
    except:
        skill_gaps = []
    
    # Get quick suggestion
    try:
        daily_suggestion = service.get_quick_recommendation(db, 30)
    except:
        daily_suggestion = None
    
    # Stats
    total = db.query(Recommendation).count()
    completed = db.query(Recommendation).filter(Recommendation.is_completed == True).count()
    dismissed = db.query(Recommendation).filter(Recommendation.is_dismissed == True).count()
    
    return RecommendationDashboard(
        active_recommendations=[RecommendationSummary.model_validate(r) for r in active_recs],
        skill_gaps=[SkillGapAnalysis(**g) for g in skill_gaps] if skill_gaps else [],
        daily_suggestion=QuickRecommendation(**daily_suggestion) if daily_suggestion else None,
        weekly_focus=skill_gaps[0].get("suggested_focus") if skill_gaps else None,
        stats={
            "total": total,
            "completed": completed,
            "dismissed": dismissed,
            "completion_rate": (completed / total * 100) if total > 0 else 0
        }
    )


@router.get("/", response_model=RecommendationsListResponse)
async def list_recommendations(
    domain: Optional[RecommendationDomain] = None,
    rec_type: Optional[RecommendationType] = None,
    priority: Optional[RecommendationPriority] = None,
    is_completed: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    List recommendations with filtering.
    
    Filter by domain, type, priority, or completion status.
    """
    query = db.query(Recommendation)
    
    # Apply filters
    if domain:
        query = query.filter(Recommendation.domain == domain)
    if rec_type:
        query = query.filter(Recommendation.rec_type == rec_type)
    if priority:
        query = query.filter(Recommendation.priority == priority)
    if is_completed is not None:
        query = query.filter(Recommendation.is_completed == is_completed)
    
    # Get counts
    total = query.count()
    pending = query.filter(
        Recommendation.is_completed == False,
        Recommendation.is_dismissed == False
    ).count()
    completed_count = db.query(Recommendation).filter(Recommendation.is_completed == True).count()
    dismissed_count = db.query(Recommendation).filter(Recommendation.is_dismissed == True).count()
    
    # Paginate
    recommendations = query.order_by(
        Recommendation.priority.desc(),
        Recommendation.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return RecommendationsListResponse(
        recommendations=recommendations,
        total=total,
        pending_count=pending,
        completed_count=completed_count,
        dismissed_count=dismissed_count
    )


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific recommendation by ID."""
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec


@router.patch("/{recommendation_id}", response_model=RecommendationResponse)
async def update_recommendation(
    recommendation_id: int,
    update: RecommendationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update recommendation status (complete/dismiss).
    
    WHY: Track which recommendations were followed.
    """
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    if update.is_completed is not None:
        rec.is_completed = update.is_completed
        if update.is_completed:
            rec.completed_at = datetime.utcnow()
    
    if update.is_dismissed is not None:
        rec.is_dismissed = update.is_dismissed
    
    db.commit()
    db.refresh(rec)
    return rec


@router.post("/{recommendation_id}/feedback", response_model=RecommendationResponse)
async def submit_feedback(
    recommendation_id: int,
    feedback: RecommendationFeedback,
    db: Session = Depends(get_db)
):
    """
    Submit feedback on a recommendation.
    
    WHY: Feedback improves future recommendations.
    Rate how helpful it was (1-5) and optionally explain why.
    """
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    rec.user_rating = feedback.user_rating
    rec.user_feedback = feedback.user_feedback
    
    db.commit()
    db.refresh(rec)
    return rec


@router.delete("/{recommendation_id}")
async def delete_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db)
):
    """Delete a recommendation."""
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    db.delete(rec)
    db.commit()
    return {"message": "Recommendation deleted"}
