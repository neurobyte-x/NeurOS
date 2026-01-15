"""
NeurOS 2.0 Schemas Package
"""

from app.schemas.user import (
    UserCreate, UserLogin, UserUpdate, UserResponse,
    TokenResponse, TokenRefresh, PasswordChange, UserStats,
)
from app.schemas.entry import (
    EntryCreate, EntryUpdate, EntryResponse, EntryWithDecay,
    EntryListResponse, EntryFilter, ReflectionCreate, ReflectionResponse,
)
from app.schemas.pattern import (
    PatternCreate, PatternUpdate, PatternResponse, PatternWithTemplates,
    PatternListResponse, PatternTemplateCreate, PatternTemplateResponse,
)
from app.schemas.review import (
    ReviewItemCreate, ReviewItemResponse, ReviewItemWithData,
    ReviewSubmit, ReviewResult, ReviewQueueStats, ReviewQueue,
    FlashCodingProblem, FlashCodingSubmission, FlashCodingResult,
)
from app.schemas.decay import (
    DecayStatusResponse, DecayStatusWithItem, DecayOverview,
    DecayCriticalAlert, DecayDashboard, PracticeHeatmap, HeatmapDay,
)
from app.schemas.standup import (
    DailyPlan, DailyPlanStats, SuggestedChallenge, WeakAreaAlert,
    StudySessionPlan, SessionStart, SessionEnd, WeeklyReport,
)
from app.schemas.analytics import (
    DailyActivity, WeeklyTrend, MonthlyOverview, DomainStats,
    DomainComparison, PatternAnalytics, LearningInsights,
    ProgressReport, AnalyticsDashboard,
)
from app.schemas.graph import (
    KnowledgeNodeCreate, KnowledgeNodeUpdate, KnowledgeNodeResponse,
    KnowledgeEdgeCreate, KnowledgeEdgeResponse, KnowledgeGraph,
    GraphNode, GraphEdge, GraphFilter,
)
