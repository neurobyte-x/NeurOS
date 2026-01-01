"""
Recommendation Service - AI-powered personalized learning suggestions.

WHY: Beginners and intermediate developers often don't know WHAT to learn next.
This service analyzes their learning history, identifies gaps, and provides
actionable recommendations tailored to their goals.

Built with Gemini 2.5 Flash for intelligent recommendation generation.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from config import settings
from models.entry import Entry, EntryType
from models.reflection import Reflection
from models.pattern import Pattern
from models.recommendation import (
    Recommendation, RecommendationType, 
    RecommendationPriority, RecommendationDomain
)


class GeneratedRecommendation(BaseModel):
    """Single recommendation from AI."""
    title: str = Field(description="Clear, actionable title")
    description: str = Field(description="Detailed explanation of what to do")
    rec_type: str = Field(description="One of: problem, concept, resource, practice, revision, project, challenge")
    domain: str = Field(description="One of: dsa, cp, backend, ai_ml, system_design, general")
    priority: str = Field(description="One of: critical, high, medium, low")
    reasoning: str = Field(description="WHY this is recommended based on user's history")
    resource_url: Optional[str] = Field(None, description="Link to resource if applicable")
    resource_name: Optional[str] = Field(None, description="Name of resource")
    difficulty_level: int = Field(description="Difficulty 1-5")
    estimated_minutes: int = Field(description="Estimated time in minutes")
    related_patterns: List[str] = Field(description="Related pattern tags")
    prerequisites: List[str] = Field(description="What user should know first")


class RecommendationSet(BaseModel):
    """Set of recommendations from AI."""
    recommendations: List[GeneratedRecommendation]
    skill_analysis: dict = Field(description="Analysis of user's current skill levels")
    weekly_focus: str = Field(description="Suggested focus area for the week")


class SkillGapResult(BaseModel):
    """Skill gap analysis result."""
    domain: str
    current_level: int
    gaps: List[str]
    strengths: List[str]
    improvement_areas: List[str]
    suggested_focus: str


class RecommendationService:
    """
    Service for generating personalized learning recommendations.
    
    WHY: Combines user's learning history with AI to provide
    targeted, actionable recommendations.
    """
    
    def __init__(self):
        if settings.GEMINI_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-preview-05-20",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.4,  # Slightly creative for recommendations
            )
            self.parser = JsonOutputParser(pydantic_object=RecommendationSet)
            self._recommendation_chain = None
        else:
            self.llm = None
    
    def _get_user_context(self, db: Session) -> dict:
        """
        Gather user's learning history for AI context.
        
        Returns comprehensive profile of user's learning journey.
        """
        entry_stats = {}
        for entry_type in EntryType:
            count = db.query(Entry).filter(
                Entry.entry_type == entry_type,
                Entry.is_complete == True
            ).count()
            entry_stats[entry_type.value] = count
        
        recent_entries = db.query(Entry).filter(
            Entry.is_complete == True,
            Entry.created_at >= datetime.utcnow() - timedelta(days=30)
        ).order_by(Entry.created_at.desc()).limit(20).all()
        
        recent_summary = []
        for entry in recent_entries:
            summary = {
                "type": entry.entry_type.value,
                "title": entry.title,
                "difficulty": entry.difficulty,
                "days_ago": (datetime.utcnow() - entry.created_at).days
            }
            if entry.reflection:
                summary["blocker"] = entry.reflection.initial_blocker[:100]
                summary["pattern"] = entry.reflection.key_pattern[:100]
            recent_summary.append(summary)
        
        blockers = db.query(Reflection.initial_blocker).join(Entry).filter(
            Entry.is_complete == True
        ).limit(50).all()
        blocker_texts = [b[0][:100] for b in blockers if b[0]]
        
        patterns = db.query(Pattern).filter(
            Pattern.usage_count > 0
        ).order_by(Pattern.usage_count.desc()).limit(20).all()
        pattern_names = [p.name for p in patterns]
        
        difficulties = db.query(Entry.difficulty).filter(
            Entry.is_complete == True,
            Entry.difficulty.isnot(None)
        ).all()
        avg_difficulty = sum(d[0] for d in difficulties) / len(difficulties) if difficulties else 3
        
        return {
            "entry_stats": entry_stats,
            "total_entries": sum(entry_stats.values()),
            "recent_entries": recent_summary,
            "common_blockers": blocker_texts[:10],
            "learned_patterns": pattern_names,
            "average_difficulty": round(avg_difficulty, 1),
            "active_days": len(set(e.created_at.date() for e in recent_entries))
        }
    
    def _build_recommendation_chain(self):
        """Build LangChain for generating recommendations."""
        
        system_prompt = """You are an expert mentor for developers learning DSA, competitive programming, 
backend development, and AI/ML. Generate personalized learning recommendations based on the user's history.

USER PROFILE:
{user_context}

GENERATION GUIDELINES:
1. **Analyze Patterns**: Look at what they've worked on, where they struggled, what patterns they've learned
2. **Identify Gaps**: What fundamental concepts might they be missing?
3. **Build Progressively**: Recommendations should build on what they know
4. **Mix Types**: Include different types (problems, concepts, resources, revisions)
5. **Be Specific**: Give specific problem names, resource links when possible
6. **Explain WHY**: The reasoning field is crucial - explain why THIS recommendation for THIS user

DIFFICULTY MAPPING:
- Level 1-2: Beginner (basic concepts, easy LeetCode)
- Level 3: Intermediate (medium LeetCode, real projects)
- Level 4-5: Advanced (hard problems, system design)

RESOURCE SUGGESTIONS:
- DSA/CP: LeetCode, NeetCode, Codeforces, AtCoder
- Backend: FastAPI docs, Real Python, System Design Primer
- AI/ML: Fast.ai, Andrew Ng courses, Papers with Code

{format_instructions}

Generate {count} recommendations based on the user's current focus: {focus}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Generate personalized recommendations for the domains: {domains}")
        ])
        
        return prompt | self.llm | self.parser
    
    def generate_recommendations(
        self,
        db: Session,
        domains: Optional[List[str]] = None,
        count: int = 5,
        current_focus: Optional[str] = None,
        difficulty_preference: Optional[int] = None
    ) -> List[dict]:
        """
        Generate personalized recommendations.
        
        Args:
            db: Database session
            domains: Focus areas (None = all)
            count: Number of recommendations
            current_focus: What user is currently working on
            difficulty_preference: Preferred difficulty level
            
        Returns:
            List of recommendation dictionaries
        """
        if not self.llm:
            raise ValueError("Gemini API key not configured")
        
        user_context = self._get_user_context(db)
        
        if difficulty_preference:
            user_context["difficulty_preference"] = difficulty_preference
        
        if not self._recommendation_chain:
            self._recommendation_chain = self._build_recommendation_chain()
        
        domains_str = ", ".join(domains) if domains else "all areas"
        focus_str = current_focus or "general improvement"
        
        try:
            result = self._recommendation_chain.invoke({
                "user_context": json.dumps(user_context, indent=2),
                "format_instructions": self.parser.get_format_instructions(),
                "count": count,
                "focus": focus_str,
                "domains": domains_str
            })
            
            return self._process_recommendations(result, db)
            
        except Exception as e:
            raise ValueError(f"Recommendation generation failed: {str(e)}")
    
    def _process_recommendations(self, result: dict, db: Session) -> List[dict]:
        """Process and save recommendations to database."""
        recommendations = []
        
        for rec in result.get("recommendations", []):
            rec_type = self._map_rec_type(rec.get("rec_type", "concept"))
            domain = self._map_domain(rec.get("domain", "general"))
            priority = self._map_priority(rec.get("priority", "medium"))
            
            db_rec = Recommendation(
                title=rec.get("title", "Untitled"),
                description=rec.get("description", ""),
                rec_type=rec_type,
                domain=domain,
                priority=priority,
                reasoning=rec.get("reasoning", "Based on your learning history"),
                resource_url=rec.get("resource_url"),
                resource_name=rec.get("resource_name"),
                difficulty_level=rec.get("difficulty_level", 3),
                estimated_minutes=rec.get("estimated_minutes", 30),
                related_patterns=rec.get("related_patterns", []),
                prerequisites=rec.get("prerequisites", []),
                confidence_score=0.8,
                generated_by="gemini-2.5-flash"
            )
            
            db.add(db_rec)
            recommendations.append(rec)
        
        db.commit()
        return recommendations
    
    def _map_rec_type(self, type_str: str) -> RecommendationType:
        """Map string to RecommendationType enum."""
        mapping = {
            "problem": RecommendationType.PROBLEM,
            "concept": RecommendationType.CONCEPT,
            "resource": RecommendationType.RESOURCE,
            "practice": RecommendationType.PRACTICE,
            "revision": RecommendationType.REVISION,
            "project": RecommendationType.PROJECT,
            "challenge": RecommendationType.CHALLENGE,
        }
        return mapping.get(type_str.lower(), RecommendationType.CONCEPT)
    
    def _map_domain(self, domain_str: str) -> RecommendationDomain:
        """Map string to RecommendationDomain enum."""
        mapping = {
            "dsa": RecommendationDomain.DSA,
            "cp": RecommendationDomain.CP,
            "backend": RecommendationDomain.BACKEND,
            "ai_ml": RecommendationDomain.AI_ML,
            "system_design": RecommendationDomain.SYSTEM_DESIGN,
            "general": RecommendationDomain.GENERAL,
        }
        return mapping.get(domain_str.lower(), RecommendationDomain.GENERAL)
    
    def _map_priority(self, priority_str: str) -> RecommendationPriority:
        """Map string to RecommendationPriority enum."""
        mapping = {
            "critical": RecommendationPriority.CRITICAL,
            "high": RecommendationPriority.HIGH,
            "medium": RecommendationPriority.MEDIUM,
            "low": RecommendationPriority.LOW,
        }
        return mapping.get(priority_str.lower(), RecommendationPriority.MEDIUM)
    
    def get_quick_recommendation(
        self, 
        db: Session, 
        available_minutes: int = 30,
        domain: Optional[str] = None
    ) -> dict:
        """
        Get a single quick recommendation for right now.
        
        WHY: Sometimes you just want to know "what should I do in the next 30 mins?"
        """
        if not self.llm:
            raise ValueError("Gemini API key not configured")
        
        user_context = self._get_user_context(db)
        
        quick_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a quick learning advisor. Based on the user's profile, 
suggest ONE thing they can do right now in {minutes} minutes.

USER PROFILE:
{context}

Be specific. If it's a problem, name it. If it's a concept, name it.
Focus on: {domain}

Return JSON:
{{
    "title": "specific action to take",
    "description": "brief explanation",
    "rec_type": "problem|concept|resource|practice",
    "domain": "dsa|cp|backend|ai_ml|general",
    "reasoning": "why this specifically",
    "resource_url": "link if applicable",
    "estimated_minutes": {minutes}
}}"""),
            ("human", "What should I do right now?")
        ])
        
        chain = quick_prompt | self.llm
        
        result = chain.invoke({
            "minutes": available_minutes,
            "context": json.dumps(user_context),
            "domain": domain or "anything"
        })
        
        try:
            import re
            json_match = re.search(r'\{.*\}', result.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "title": "Review a past entry",
            "description": "Go through your recent entries and reinforce the patterns",
            "rec_type": "revision",
            "domain": "general",
            "reasoning": "Revision strengthens learning",
            "estimated_minutes": available_minutes
        }
    
    def analyze_skill_gaps(self, db: Session) -> List[dict]:
        """
        Analyze user's skill gaps across domains.
        
        Returns analysis of strengths, weaknesses, and focus areas.
        """
        if not self.llm:
            raise ValueError("Gemini API key not configured")
        
        user_context = self._get_user_context(db)
        
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze this developer's skill levels based on their learning history.

USER DATA:
{context}

For each domain (DSA, CP, Backend, AI/ML), provide:
1. Estimated current level (1-10)
2. Identified gaps (what they seem to be missing)
3. Strengths (what they're doing well)
4. Areas to improve
5. Suggested next focus

Return JSON array:
[
    {{
        "domain": "dsa",
        "current_level": 5,
        "gaps": ["dynamic programming", "graph algorithms"],
        "strengths": ["arrays", "basic recursion"],
        "improvement_areas": ["complexity analysis", "optimization"],
        "suggested_focus": "Start with 2D DP problems"
    }},
    ...
]"""),
            ("human", "Analyze my skill gaps")
        ])
        
        chain = analysis_prompt | self.llm
        
        result = chain.invoke({
            "context": json.dumps(user_context)
        })
        
        try:
            import re
            json_match = re.search(r'\[.*\]', result.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return [
            {
                "domain": "general",
                "current_level": 5,
                "gaps": ["Need more data to analyze"],
                "strengths": ["Consistent practice"],
                "improvement_areas": ["Keep logging entries"],
                "suggested_focus": "Continue building your learning history"
            }
        ]


_recommendation_service: Optional[RecommendationService] = None


def get_recommendation_service() -> RecommendationService:
    """Get or create the recommendation service singleton."""
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service
