"""
Learning Plan Service - AI-powered structured roadmaps.

WHY: Random learning doesn't work. Beginners need structured paths with:
- Clear milestones
- Daily/weekly tasks
- Progress tracking
- Adaptation based on performance

Built with Gemini 2.5 Flash for intelligent plan generation.
"""

import json
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from config import settings
from models.entry import Entry, EntryType
from models.learning_plan import (
    LearningPlan, PlanMilestone, WeeklySchedule, DailyTask,
    PlanType, PlanStatus, MilestoneStatus
)


# === Pydantic models for AI output ===

class GeneratedMilestone(BaseModel):
    """Milestone from AI."""
    title: str
    description: str
    topics: List[str]
    skills_to_gain: List[str]
    success_criteria: str
    estimated_days: int
    recommended_resources: List[dict]
    recommended_problems: List[dict]


class GeneratedWeek(BaseModel):
    """Weekly schedule from AI."""
    week_number: int
    theme: str
    focus_areas: List[str]
    daily_tasks: Dict[str, List[dict]]  # day -> tasks
    weekly_goals: List[str]
    problems_to_solve: int
    concepts_to_learn: int


class GeneratedPlan(BaseModel):
    """Complete plan from AI."""
    title: str
    description: str
    target_outcome: str
    milestones: List[GeneratedMilestone]
    weekly_schedules: List[GeneratedWeek]
    initial_assessment: dict
    success_metrics: List[str]


class LearningPlanService:
    """
    Service for generating and managing learning plans.
    
    WHY: Transforms vague goals into actionable daily tasks.
    """
    
    def __init__(self):
        if settings.GEMINI_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-preview-05-20",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.3,  # More structured output
            )
        else:
            self.llm = None
    
    def _get_user_history(self, db: Session) -> dict:
        """Get user's learning history for plan context."""
        
        # Entry counts by type
        entry_stats = {}
        for entry_type in EntryType:
            count = db.query(Entry).filter(
                Entry.entry_type == entry_type,
                Entry.is_complete == True
            ).count()
            entry_stats[entry_type.value] = count
        
        # Average difficulty
        avg_diff = db.query(func.avg(Entry.difficulty)).filter(
            Entry.is_complete == True,
            Entry.difficulty.isnot(None)
        ).scalar() or 3.0
        
        # Recent topics
        recent_entries = db.query(Entry.title, Entry.entry_type).filter(
            Entry.is_complete == True,
            Entry.created_at >= datetime.utcnow() - timedelta(days=30)
        ).limit(20).all()
        
        recent_topics = [{"title": e[0], "type": e[1].value} for e in recent_entries]
        
        return {
            "entry_stats": entry_stats,
            "total_entries": sum(entry_stats.values()),
            "average_difficulty": round(avg_diff, 1),
            "recent_topics": recent_topics
        }
    
    def generate_plan(
        self,
        db: Session,
        plan_type: PlanType,
        primary_goal: str,
        target_weeks: int = 12,
        daily_time_minutes: int = 60,
        weekly_days: int = 5,
        current_levels: Optional[dict] = None,
        target_levels: Optional[dict] = None,
        focus_areas: Optional[List[str]] = None,
        preferred_resources: Optional[List[str]] = None
    ) -> LearningPlan:
        """
        Generate a comprehensive learning plan.
        
        Args:
            db: Database session
            plan_type: Type of plan
            primary_goal: Main objective
            target_weeks: Duration
            daily_time_minutes: Available time per day
            weekly_days: Days per week
            current_levels: Current skill levels
            target_levels: Target skill levels
            focus_areas: Specific topics to focus on
            preferred_resources: Preferred learning resources
            
        Returns:
            Created LearningPlan with milestones and schedules
        """
        if not self.llm:
            raise ValueError("Gemini API key not configured")
        
        user_history = self._get_user_history(db)
        
        # Build the generation prompt
        plan_prompt = self._build_plan_prompt()
        
        # Generate plan
        try:
            result = plan_prompt | self.llm
            response = result.invoke({
                "plan_type": plan_type.value,
                "primary_goal": primary_goal,
                "target_weeks": target_weeks,
                "daily_minutes": daily_time_minutes,
                "weekly_days": weekly_days,
                "current_levels": json.dumps(current_levels or {}),
                "target_levels": json.dumps(target_levels or {}),
                "focus_areas": json.dumps(focus_areas or []),
                "preferred_resources": json.dumps(preferred_resources or ["LeetCode", "NeetCode", "Real Python"]),
                "user_history": json.dumps(user_history)
            })
            
            # Parse JSON from response
            plan_data = self._parse_plan_response(response.content)
            
            # Create plan in database
            return self._create_plan_in_db(
                db=db,
                plan_data=plan_data,
                plan_type=plan_type,
                primary_goal=primary_goal,
                target_weeks=target_weeks,
                daily_time_minutes=daily_time_minutes,
                weekly_days=weekly_days,
                current_levels=current_levels,
                target_levels=target_levels
            )
            
        except Exception as e:
            raise ValueError(f"Plan generation failed: {str(e)}")
    
    def _build_plan_prompt(self) -> ChatPromptTemplate:
        """Build the plan generation prompt."""
        
        system_prompt = """You are an expert learning coach creating personalized study plans.
Generate a detailed, actionable learning plan.

PLAN CONTEXT:
- Type: {plan_type}
- Goal: {primary_goal}
- Duration: {target_weeks} weeks
- Daily time: {daily_minutes} minutes
- Days per week: {weekly_days}
- Current levels: {current_levels}
- Target levels: {target_levels}
- Focus areas: {focus_areas}
- Preferred resources: {preferred_resources}

USER HISTORY:
{user_history}

GENERATION RULES:
1. **Progressive Difficulty**: Start easy, build up
2. **Spaced Repetition**: Include revision of earlier topics
3. **Practical Focus**: 70% practice, 30% theory
4. **Specific Resources**: Name specific problems, videos, articles
5. **Realistic Timing**: Account for the daily time available
6. **Clear Milestones**: Each milestone = clear skill gained

FOR DSA/CP PLANS:
- Follow NeetCode roadmap structure
- Include specific LeetCode problem numbers
- Mix pattern types (arrays, strings, trees, graphs, DP)

FOR BACKEND PLANS:
- Start with fundamentals (HTTP, REST, databases)
- Include mini-projects
- Cover both theory and implementation

FOR AI/ML PLANS:
- Math foundations first
- Hands-on with real datasets
- Progress from classical ML to deep learning

Return JSON:
{{
    "title": "catchy plan title",
    "description": "overview of the plan",
    "target_outcome": "what success looks like",
    "milestones": [
        {{
            "title": "milestone title",
            "description": "what this covers",
            "topics": ["topic1", "topic2"],
            "skills_to_gain": ["skill1", "skill2"],
            "success_criteria": "how to know you're done",
            "estimated_days": 14,
            "recommended_resources": [
                {{"name": "resource", "url": "link", "type": "video|article|course"}}
            ],
            "recommended_problems": [
                {{"name": "Two Sum", "url": "leetcode.com/problems/two-sum", "difficulty": 1}}
            ]
        }}
    ],
    "weekly_schedules": [
        {{
            "week_number": 1,
            "theme": "Arrays & Hashing Fundamentals",
            "focus_areas": ["arrays", "hash maps"],
            "daily_tasks": {{
                "monday": [
                    {{"title": "task", "type": "video|problem|article|practice", "estimated_minutes": 30, "resource_url": "link"}}
                ],
                "tuesday": [...],
                ...
            }},
            "weekly_goals": ["Solve 5 easy array problems", "Understand hash map time complexity"],
            "problems_to_solve": 5,
            "concepts_to_learn": 2
        }}
    ],
    "success_metrics": ["metric1", "metric2"]
}}"""

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Generate my personalized learning plan")
        ])
    
    def _parse_plan_response(self, content: str) -> dict:
        """Parse JSON from AI response."""
        import re
        
        # Try to find JSON in response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Return default structure if parsing fails
        return {
            "title": "Learning Plan",
            "description": "Generated learning plan",
            "target_outcome": "Improved skills",
            "milestones": [],
            "weekly_schedules": [],
            "success_metrics": []
        }
    
    def _create_plan_in_db(
        self,
        db: Session,
        plan_data: dict,
        plan_type: PlanType,
        primary_goal: str,
        target_weeks: int,
        daily_time_minutes: int,
        weekly_days: int,
        current_levels: Optional[dict],
        target_levels: Optional[dict]
    ) -> LearningPlan:
        """Create the plan and related objects in database."""
        
        start_date = date.today()
        target_end_date = start_date + timedelta(weeks=target_weeks)
        
        # Create main plan
        plan = LearningPlan(
            title=plan_data.get("title", f"{plan_type.value.title()} Plan"),
            description=plan_data.get("description", ""),
            plan_type=plan_type,
            status=PlanStatus.DRAFT,
            primary_goal=primary_goal,
            target_outcome=plan_data.get("target_outcome"),
            start_date=start_date,
            target_end_date=target_end_date,
            daily_time_minutes=daily_time_minutes,
            weekly_days=weekly_days,
            initial_dsa_level=current_levels.get("dsa") if current_levels else None,
            initial_cp_level=current_levels.get("cp") if current_levels else None,
            initial_backend_level=current_levels.get("backend") if current_levels else None,
            initial_ai_ml_level=current_levels.get("ai_ml") if current_levels else None,
            target_dsa_level=target_levels.get("dsa") if target_levels else None,
            target_cp_level=target_levels.get("cp") if target_levels else None,
            target_backend_level=target_levels.get("backend") if target_levels else None,
            target_ai_ml_level=target_levels.get("ai_ml") if target_levels else None,
            generated_by="gemini-2.5-flash"
        )
        
        db.add(plan)
        db.flush()  # Get the plan ID
        
        # Create milestones
        milestones_data = plan_data.get("milestones", [])
        for idx, ms in enumerate(milestones_data):
            milestone = PlanMilestone(
                plan_id=plan.id,
                title=ms.get("title", f"Milestone {idx + 1}"),
                description=ms.get("description", ""),
                order_index=idx,
                topics=ms.get("topics", []),
                skills_to_gain=ms.get("skills_to_gain", []),
                success_criteria=ms.get("success_criteria"),
                estimated_days=ms.get("estimated_days", 7),
                recommended_resources=ms.get("recommended_resources", []),
                recommended_problems=ms.get("recommended_problems", []),
                status=MilestoneStatus.NOT_STARTED
            )
            db.add(milestone)
        
        plan.total_milestones = len(milestones_data)
        
        # Create weekly schedules
        schedules_data = plan_data.get("weekly_schedules", [])
        for ws in schedules_data:
            week_num = ws.get("week_number", 1)
            week_start = start_date + timedelta(weeks=week_num - 1)
            week_end = week_start + timedelta(days=6)
            
            schedule = WeeklySchedule(
                plan_id=plan.id,
                week_number=week_num,
                week_start_date=week_start,
                week_end_date=week_end,
                theme=ws.get("theme"),
                focus_areas=ws.get("focus_areas", []),
                daily_tasks=ws.get("daily_tasks", {}),
                weekly_goals=ws.get("weekly_goals", []),
                problems_to_solve=ws.get("problems_to_solve", 0),
                concepts_to_learn=ws.get("concepts_to_learn", 0)
            )
            db.add(schedule)
        
        db.commit()
        db.refresh(plan)
        
        return plan
    
    def get_todays_tasks(self, db: Session) -> dict:
        """Get all tasks scheduled for today across active plans."""
        
        today = date.today()
        day_name = today.strftime("%A").lower()
        
        # Get active plans
        active_plans = db.query(LearningPlan).filter(
            LearningPlan.status == PlanStatus.ACTIVE
        ).all()
        
        all_tasks = []
        plans_involved = []
        
        for plan in active_plans:
            # Find current week's schedule
            current_schedule = db.query(WeeklySchedule).filter(
                WeeklySchedule.plan_id == plan.id,
                WeeklySchedule.week_start_date <= today,
                WeeklySchedule.week_end_date >= today
            ).first()
            
            if current_schedule and current_schedule.daily_tasks:
                day_tasks = current_schedule.daily_tasks.get(day_name, [])
                for task in day_tasks:
                    task["plan_id"] = plan.id
                    task["plan_title"] = plan.title
                    all_tasks.append(task)
                
                if day_tasks:
                    plans_involved.append({
                        "id": plan.id,
                        "title": plan.title,
                        "plan_type": plan.plan_type.value
                    })
        
        return {
            "date": today.isoformat(),
            "day": day_name,
            "total_tasks": len(all_tasks),
            "tasks": all_tasks,
            "estimated_total_minutes": sum(t.get("estimated_minutes", 30) for t in all_tasks),
            "plans_involved": plans_involved
        }
    
    def adapt_plan(
        self,
        db: Session,
        plan_id: int,
        reason: str,
        new_daily_time: Optional[int] = None,
        extend_weeks: Optional[int] = None,
        shift_focus: Optional[List[str]] = None
    ) -> LearningPlan:
        """
        Adapt a plan based on user's progress or changing needs.
        
        WHY: Life happens. Plans should be flexible.
        """
        plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
        if not plan:
            raise ValueError("Plan not found")
        
        # Update time if specified
        if new_daily_time:
            plan.daily_time_minutes = new_daily_time
        
        # Extend deadline if needed
        if extend_weeks and plan.target_end_date:
            plan.target_end_date = plan.target_end_date + timedelta(weeks=extend_weeks)
        
        # Record adaptation
        plan.last_adapted_at = datetime.utcnow()
        plan.adaptation_notes = f"{plan.adaptation_notes or ''}\n[{datetime.utcnow().date()}] {reason}"
        
        # If AI is available, regenerate remaining weeks
        if self.llm and shift_focus:
            # This would regenerate future weekly schedules
            # For now, just update the plan record
            pass
        
        db.commit()
        db.refresh(plan)
        return plan
    
    def calculate_progress(self, db: Session, plan_id: int) -> dict:
        """Calculate detailed progress for a plan."""
        
        plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
        if not plan:
            raise ValueError("Plan not found")
        
        # Milestone progress
        completed_milestones = db.query(PlanMilestone).filter(
            PlanMilestone.plan_id == plan_id,
            PlanMilestone.status == MilestoneStatus.COMPLETED
        ).count()
        
        total_milestones = db.query(PlanMilestone).filter(
            PlanMilestone.plan_id == plan_id
        ).count()
        
        # Weekly progress
        completed_weeks = db.query(WeeklySchedule).filter(
            WeeklySchedule.plan_id == plan_id,
            WeeklySchedule.is_completed == True
        ).count()
        
        total_weeks = db.query(WeeklySchedule).filter(
            WeeklySchedule.plan_id == plan_id
        ).count()
        
        # Calculate current week
        if plan.start_date:
            days_since_start = (date.today() - plan.start_date).days
            current_week = (days_since_start // 7) + 1
        else:
            current_week = 1
        
        # Update plan progress
        progress_pct = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
        plan.progress_percentage = progress_pct
        plan.completed_milestones = completed_milestones
        plan.current_week = current_week
        
        db.commit()
        
        return {
            "plan_id": plan_id,
            "progress_percentage": progress_pct,
            "milestones": {
                "completed": completed_milestones,
                "total": total_milestones
            },
            "weeks": {
                "completed": completed_weeks,
                "total": total_weeks,
                "current": current_week
            },
            "days_remaining": (plan.target_end_date - date.today()).days if plan.target_end_date else None,
            "on_track": current_week <= total_weeks
        }


# Singleton instance
_plan_service: Optional[LearningPlanService] = None


def get_plan_service() -> LearningPlanService:
    """Get or create the plan service singleton."""
    global _plan_service
    if _plan_service is None:
        _plan_service = LearningPlanService()
    return _plan_service
