"""
Learning Plan model - Structured roadmaps for skill development.

WHY: Beginners/intermediate developers need structured paths, not just random problems.
A learning plan provides:
1. Clear goals with deadlines
2. Milestones to track progress
3. Daily/weekly tasks
4. Adaptation based on performance

DESIGN: Plans are AI-generated based on user's current level, goals, 
available time, and learning history. They adapt over time.
"""

import enum
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date,
    Enum, Boolean, Float, JSON, ForeignKey
)
from sqlalchemy.orm import relationship

from database import Base


class PlanType(enum.Enum):
    """Types of learning plans."""
    DSA_FUNDAMENTALS = "dsa_fundamentals"       # Basics of DSA
    CP_BEGINNER = "cp_beginner"                  # Start competitive programming
    CP_INTERMEDIATE = "cp_intermediate"          # Level up in CP
    INTERVIEW_PREP = "interview_prep"            # Technical interview focus
    BACKEND_BASICS = "backend_basics"            # Backend fundamentals
    BACKEND_ADVANCED = "backend_advanced"        # Advanced backend
    AI_ML_START = "ai_ml_start"                  # Getting into AI/ML
    SYSTEM_DESIGN = "system_design"              # System design prep
    CUSTOM = "custom"                            # User-defined goals


class PlanStatus(enum.Enum):
    """Plan lifecycle status."""
    DRAFT = "draft"              # Being created
    ACTIVE = "active"            # Currently following
    PAUSED = "paused"            # Temporarily stopped
    COMPLETED = "completed"      # Successfully finished
    ABANDONED = "abandoned"      # Given up


class MilestoneStatus(enum.Enum):
    """Milestone completion status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class LearningPlan(Base):
    """
    AI-generated structured learning plan.
    
    WHY: A roadmap beats random wandering. This provides:
    - Clear direction
    - Measurable progress
    - Accountability
    - Adaptability based on performance
    """
    __tablename__ = "learning_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Plan identity
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    plan_type = Column(Enum(PlanType), nullable=False, index=True)
    status = Column(Enum(PlanStatus), default=PlanStatus.DRAFT, index=True)
    
    # Goals and scope
    primary_goal = Column(Text, nullable=False)  # Main objective
    secondary_goals = Column(JSON, default=list)  # Additional objectives
    target_outcome = Column(Text, nullable=True)  # What success looks like
    
    # Time parameters
    start_date = Column(Date, nullable=True)
    target_end_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    daily_time_minutes = Column(Integer, default=60)  # Available time per day
    weekly_days = Column(Integer, default=5)          # Days per week
    
    # Current level assessment (1-10 scale)
    initial_dsa_level = Column(Integer, nullable=True)
    initial_cp_level = Column(Integer, nullable=True)
    initial_backend_level = Column(Integer, nullable=True)
    initial_ai_ml_level = Column(Integer, nullable=True)
    
    # Target levels
    target_dsa_level = Column(Integer, nullable=True)
    target_cp_level = Column(Integer, nullable=True)
    target_backend_level = Column(Integer, nullable=True)
    target_ai_ml_level = Column(Integer, nullable=True)
    
    # Progress tracking
    total_milestones = Column(Integer, default=0)
    completed_milestones = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    current_week = Column(Integer, default=1)
    
    # Adaptation
    last_adapted_at = Column(DateTime, nullable=True)
    adaptation_notes = Column(Text, nullable=True)
    
    # Generation metadata
    generated_by = Column(String(100), default="gemini")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    milestones = relationship(
        "PlanMilestone",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanMilestone.order_index"
    )
    
    weekly_schedules = relationship(
        "WeeklySchedule",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="WeeklySchedule.week_number"
    )


class PlanMilestone(Base):
    """
    Milestone within a learning plan.
    
    WHY: Break big goals into achievable chunks.
    Each milestone should feel accomplishable in 1-2 weeks.
    """
    __tablename__ = "plan_milestones"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=False)
    
    # Milestone details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)  # Order in plan
    
    # Scope
    topics = Column(JSON, default=list)           # Topics to cover
    skills_to_gain = Column(JSON, default=list)   # Expected skills
    success_criteria = Column(Text, nullable=True)  # How to know you're done
    
    # Time
    estimated_days = Column(Integer, nullable=True)
    target_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    
    # Status
    status = Column(Enum(MilestoneStatus), default=MilestoneStatus.NOT_STARTED)
    
    # Resources
    recommended_resources = Column(JSON, default=list)  # Links, courses, etc.
    recommended_problems = Column(JSON, default=list)   # Specific problems to solve
    
    # Progress
    tasks_total = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    
    # Reflection (after completion)
    reflection_notes = Column(Text, nullable=True)
    difficulty_rating = Column(Integer, nullable=True)  # How hard was it (1-5)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    plan = relationship("LearningPlan", back_populates="milestones")


class WeeklySchedule(Base):
    """
    Weekly breakdown of tasks within a plan.
    
    WHY: Daily/weekly structure prevents overwhelm and ensures consistent progress.
    """
    __tablename__ = "weekly_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=False)
    
    # Week identity
    week_number = Column(Integer, nullable=False)
    week_start_date = Column(Date, nullable=True)
    week_end_date = Column(Date, nullable=True)
    
    # Focus for this week
    theme = Column(String(200), nullable=True)   # E.g., "Arrays & Hashing"
    focus_areas = Column(JSON, default=list)     # Main topics
    
    # Daily tasks (JSON structure for flexibility)
    # Format: {day: [{task, type, estimated_minutes, resource_url}]}
    daily_tasks = Column(JSON, default=dict)
    
    # Goals for the week
    weekly_goals = Column(JSON, default=list)
    problems_to_solve = Column(Integer, default=0)
    concepts_to_learn = Column(Integer, default=0)
    
    # Tracking
    is_completed = Column(Boolean, default=False)
    completion_notes = Column(Text, nullable=True)
    actual_time_spent = Column(Integer, nullable=True)  # Total minutes
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    plan = relationship("LearningPlan", back_populates="weekly_schedules")


class DailyTask(Base):
    """
    Individual task to complete on a specific day.
    
    WHY: Granular tracking of daily activities within a plan.
    """
    __tablename__ = "daily_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("weekly_schedules.id"), nullable=False)
    
    # Task details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False)  # problem, video, article, practice
    
    # When
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    scheduled_date = Column(Date, nullable=True)
    
    # Resource
    resource_url = Column(String(2000), nullable=True)
    resource_name = Column(String(200), nullable=True)
    
    # Time
    estimated_minutes = Column(Integer, default=30)
    actual_minutes = Column(Integer, nullable=True)
    
    # Completion
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
