"""
AI routes for Thinking OS.

WHY: These endpoints power the conversational entry creation experience.
Users describe their experience naturally, AI extracts structure.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.ai_service import get_ai_service


router = APIRouter(prefix="/ai", tags=["AI"])


class AnalyzeRequest(BaseModel):
    """
    Request to analyze a natural language learning experience.
    
    WHY: Simple input - just describe what happened in your own words.
    The AI will extract all the structured fields.
    """
    raw_input: str = Field(
        ...,
        min_length=50,
        description="Describe your learning experience. Include what you were doing, "
                    "where you got stuck, how long it took, and what helped you solve it."
    )


class AnalyzeResponse(BaseModel):
    """
    Structured data extracted from the experience description.
    
    WHY: Returns all fields needed to create an entry with reflection.
    User can review/edit before saving.
    """
    entry_type: str
    title: str
    context: str
    initial_blocker: str
    trigger_signal: str
    key_pattern: str
    mistake_or_edge_case: str
    suggested_patterns: list[str]
    time_spent_minutes: int
    difficulty: int


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_experience(request: AnalyzeRequest):
    """
    Analyze a natural language description and extract structured reflection data.
    
    WHY: This is the magic endpoint that removes form-filling friction.
    Users describe their experience conversationally, and this endpoint
    returns structured data ready for entry creation.
    
    Example input:
    "Spent 2 hours on a leetcode two-sum problem. Was trying to find pairs 
    that add up to target. Got stuck because I was using nested loops which 
    was O(n²). Finally realized I could use a hash map to store complements.
    The key insight was that for each number, I only need to check if its 
    complement exists. Watch out for duplicates - same element can't be used twice."
    
    Returns structured data with entry_type=dsa, extracted context, blockers, etc.
    """
    ai_service = get_ai_service()
    
    try:
        result = ai_service.analyze_experience(request.raw_input)
        return AnalyzeResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"AI analysis failed. Please try again or fill fields manually. Error: {str(e)}"
        )


@router.get("/status")
async def ai_status():
    """
    Check if AI service is configured and ready.
    
    WHY: Frontend can check this to show/hide AI features.
    """
    ai_service = get_ai_service()
    return {
        "configured": ai_service.model is not None,
        "message": "AI ready" if ai_service.model else "Set GEMINI_API_KEY in .env to enable AI features"
    }
