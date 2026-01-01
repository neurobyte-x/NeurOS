"""
Learning Plan routes for Thinking OS.

WHY: Structured learning paths are essential for beginners/intermediates.
These endpoints manage AI-generated learning plans with milestones,
weekly schedules, and progress tracking.
"""

from typing import Optional, List
from datetime import date
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.learning_plan import (
    LearningPlan, PlanMilestone, WeeklySchedule, DailyTask,
    PlanType, PlanStatus, MilestoneStatus
)
from schemas.learning_plan import (
    CreatePlanRequest,
    UpdatePlanRequest,
    MilestoneUpdateRequest,
    AdaptPlanRequest,
    LearningPlanResponse,
    LearningPlanSummary,
    LearningPlanWithDetails,
    MilestoneResponse,
    WeeklyScheduleResponse,
    TodaysTasks,
    PlanDashboard,
    WeeklyProgress
)
from services.plan_service import get_plan_service


router = APIRouter(prefix="/plans", tags=["learning-plans"])


@router.post("/generate", response_model=LearningPlanResponse)
async def generate_plan(
    request: CreatePlanRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a personalized learning plan using AI.
    
    WHY: Transform vague goals into actionable daily tasks.
    
    Example: "I want to crack FAANG interviews in 3 months"
    Returns: A structured plan with milestones, weekly schedules,
    and specific problems/resources for each day.
    """
    service = get_plan_service()
    
    try:
        current_levels = {}
        if request.current_dsa_level:
            current_levels["dsa"] = request.current_dsa_level
        if request.current_cp_level:
            current_levels["cp"] = request.current_cp_level
        if request.current_backend_level:
            current_levels["backend"] = request.current_backend_level
        if request.current_ai_ml_level:
            current_levels["ai_ml"] = request.current_ai_ml_level
        
        target_levels = {}
        if request.target_dsa_level:
            target_levels["dsa"] = request.target_dsa_level
        if request.target_cp_level:
            target_levels["cp"] = request.target_cp_level
        if request.target_backend_level:
            target_levels["backend"] = request.target_backend_level
        if request.target_ai_ml_level:
            target_levels["ai_ml"] = request.target_ai_ml_level
        
        plan = service.generate_plan(
            db=db,
            plan_type=request.plan_type,
            primary_goal=request.primary_goal,
            target_weeks=request.target_weeks,
            daily_time_minutes=request.daily_time_minutes,
            weekly_days=request.weekly_days,
            current_levels=current_levels or None,
            target_levels=target_levels or None,
            focus_areas=request.focus_areas,
            preferred_resources=request.preferred_resources
        )
        
        return plan
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate plan: {str(e)}"
        )


@router.get("/dashboard", response_model=PlanDashboard)
async def get_plan_dashboard(db: Session = Depends(get_db)):
    """
    Get dashboard data for learning plans section.
    
    Returns active plans, today's tasks, weekly progress, and upcoming milestones.
    """
    service = get_plan_service()
    
    active_plans = db.query(LearningPlan).filter(
        LearningPlan.status == PlanStatus.ACTIVE
    ).order_by(LearningPlan.created_at.desc()).all()
    
    todays_tasks = service.get_todays_tasks(db)
    
    upcoming = db.query(PlanMilestone).join(LearningPlan).filter(
        LearningPlan.status == PlanStatus.ACTIVE,
        PlanMilestone.status != MilestoneStatus.COMPLETED
    ).order_by(PlanMilestone.order_index).limit(5).all()
    
    weekly_progress = []
    today = date.today()
    for plan in active_plans:
        current_schedule = db.query(WeeklySchedule).filter(
            WeeklySchedule.plan_id == plan.id,
            WeeklySchedule.week_start_date <= today,
            WeeklySchedule.week_end_date >= today
        ).first()
        
        if current_schedule:
            tasks_total = 0
            tasks_completed = 0
            for day_tasks in current_schedule.daily_tasks.values():
                tasks_total += len(day_tasks)
            
            weekly_progress.append(WeeklyProgress(
                week_number=current_schedule.week_number,
                plan_id=plan.id,
                plan_title=plan.title,
                theme=current_schedule.theme,
                tasks_total=tasks_total,
                tasks_completed=tasks_completed,
                time_spent_minutes=current_schedule.actual_time_spent or 0,
                goals_achieved=[],
                goals_pending=current_schedule.weekly_goals or []
            ))
    
    total_plans = db.query(LearningPlan).count()
    completed_plans = db.query(LearningPlan).filter(
        LearningPlan.status == PlanStatus.COMPLETED
    ).count()
    
    return PlanDashboard(
        active_plans=[LearningPlanSummary.model_validate(p) for p in active_plans],
        todays_tasks=TodaysTasks(
            date=today,
            total_tasks=todays_tasks["total_tasks"],
            completed_tasks=0,  # Would need task completion tracking
            pending_tasks=[],  # Would need proper task model
            estimated_total_minutes=todays_tasks["estimated_total_minutes"],
            plans_involved=[LearningPlanSummary.model_validate(
                db.query(LearningPlan).get(p["id"])
            ) for p in todays_tasks["plans_involved"]]
        ),
        current_week_progress=weekly_progress,
        upcoming_milestones=[MilestoneResponse.model_validate(m) for m in upcoming],
        overall_stats={
            "total_plans": total_plans,
            "active_plans": len(active_plans),
            "completed_plans": completed_plans,
            "total_milestones": db.query(PlanMilestone).count(),
            "completed_milestones": db.query(PlanMilestone).filter(
                PlanMilestone.status == MilestoneStatus.COMPLETED
            ).count()
        }
    )


@router.get("/today", response_model=dict)
async def get_todays_tasks(db: Session = Depends(get_db)):
    """
    Get all tasks scheduled for today.
    
    WHY: "What should I do today?" - answered in one call.
    """
    service = get_plan_service()
    return service.get_todays_tasks(db)


@router.get("/", response_model=List[LearningPlanSummary])
async def list_plans(
    status: Optional[PlanStatus] = None,
    plan_type: Optional[PlanType] = None,
    db: Session = Depends(get_db)
):
    """List all learning plans with optional filtering."""
    query = db.query(LearningPlan)
    
    if status:
        query = query.filter(LearningPlan.status == status)
    if plan_type:
        query = query.filter(LearningPlan.plan_type == plan_type)
    
    plans = query.order_by(LearningPlan.created_at.desc()).all()
    return plans


@router.get("/{plan_id}", response_model=LearningPlanWithDetails)
async def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get a specific plan with all milestones and schedules."""
    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    milestones = db.query(PlanMilestone).filter(
        PlanMilestone.plan_id == plan_id
    ).order_by(PlanMilestone.order_index).all()
    
    schedules = db.query(WeeklySchedule).filter(
        WeeklySchedule.plan_id == plan_id
    ).order_by(WeeklySchedule.week_number).all()
    
    return LearningPlanWithDetails(
        **LearningPlanResponse.model_validate(plan).model_dump(),
        milestones=[MilestoneResponse.model_validate(m) for m in milestones],
        weekly_schedules=[WeeklyScheduleResponse.model_validate(s) for s in schedules]
    )


@router.patch("/{plan_id}", response_model=LearningPlanResponse)
async def update_plan(
    plan_id: int,
    update: UpdatePlanRequest,
    db: Session = Depends(get_db)
):
    """Update plan settings."""
    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)
    
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/{plan_id}/activate", response_model=LearningPlanResponse)
async def activate_plan(plan_id: int, db: Session = Depends(get_db)):
    """Activate a plan to start following it."""
    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan.status = PlanStatus.ACTIVE
    if not plan.start_date:
        plan.start_date = date.today()
    
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/{plan_id}/pause", response_model=LearningPlanResponse)
async def pause_plan(plan_id: int, db: Session = Depends(get_db)):
    """Pause an active plan."""
    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan.status = PlanStatus.PAUSED
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/{plan_id}/adapt", response_model=LearningPlanResponse)
async def adapt_plan(
    plan_id: int,
    request: AdaptPlanRequest,
    db: Session = Depends(get_db)
):
    """
    Adapt a plan based on progress or changing needs.
    
    WHY: Life happens. Plans should be flexible.
    """
    service = get_plan_service()
    
    try:
        plan = service.adapt_plan(
            db=db,
            plan_id=plan_id,
            reason=request.reason,
            new_daily_time=request.new_daily_time,
            extend_weeks=request.extend_weeks,
            shift_focus=request.shift_focus
        )
        return plan
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{plan_id}/progress")
async def get_plan_progress(plan_id: int, db: Session = Depends(get_db)):
    """Get detailed progress for a plan."""
    service = get_plan_service()
    
    try:
        return service.calculate_progress(db, plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{plan_id}/milestones", response_model=List[MilestoneResponse])
async def get_milestones(plan_id: int, db: Session = Depends(get_db)):
    """Get all milestones for a plan."""
    milestones = db.query(PlanMilestone).filter(
        PlanMilestone.plan_id == plan_id
    ).order_by(PlanMilestone.order_index).all()
    return milestones


@router.patch("/{plan_id}/milestones/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    plan_id: int,
    milestone_id: int,
    update: MilestoneUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update a milestone (status, reflection, etc.)."""
    milestone = db.query(PlanMilestone).filter(
        PlanMilestone.id == milestone_id,
        PlanMilestone.plan_id == plan_id
    ).first()
    
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    if update.status:
        milestone.status = update.status
        if update.status == MilestoneStatus.COMPLETED:
            milestone.completed_date = date.today()
    
    if update.reflection_notes:
        milestone.reflection_notes = update.reflection_notes
    
    if update.difficulty_rating:
        milestone.difficulty_rating = update.difficulty_rating
    
    db.commit()
    db.refresh(milestone)
    return milestone


@router.get("/{plan_id}/weeks", response_model=List[WeeklyScheduleResponse])
async def get_weekly_schedules(plan_id: int, db: Session = Depends(get_db)):
    """Get all weekly schedules for a plan."""
    schedules = db.query(WeeklySchedule).filter(
        WeeklySchedule.plan_id == plan_id
    ).order_by(WeeklySchedule.week_number).all()
    return schedules


@router.get("/{plan_id}/weeks/{week_number}", response_model=WeeklyScheduleResponse)
async def get_week_schedule(
    plan_id: int,
    week_number: int,
    db: Session = Depends(get_db)
):
    """Get a specific week's schedule."""
    schedule = db.query(WeeklySchedule).filter(
        WeeklySchedule.plan_id == plan_id,
        WeeklySchedule.week_number == week_number
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Week schedule not found")
    return schedule


@router.post("/{plan_id}/weeks/{week_number}/complete")
async def complete_week(
    plan_id: int,
    week_number: int,
    notes: Optional[str] = None,
    time_spent: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Mark a week as completed."""
    schedule = db.query(WeeklySchedule).filter(
        WeeklySchedule.plan_id == plan_id,
        WeeklySchedule.week_number == week_number
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Week schedule not found")
    
    schedule.is_completed = True
    schedule.completion_notes = notes
    schedule.actual_time_spent = time_spent
    
    db.commit()
    return {"message": f"Week {week_number} marked as complete"}


@router.delete("/{plan_id}")
async def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    """Delete a learning plan and all related data."""
    plan = db.query(LearningPlan).filter(LearningPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    db.delete(plan)
    db.commit()
    return {"message": "Plan deleted"}
