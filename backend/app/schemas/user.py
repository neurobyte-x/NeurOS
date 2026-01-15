"""
NeurOS 2.0 User Schemas

Pydantic schemas for user authentication and profile.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# =============================================================================
# Base Schemas
# =============================================================================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: Optional[str] = None


# =============================================================================
# Request Schemas
# =============================================================================

class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    daily_review_goal: Optional[int] = Field(None, ge=1, le=100)
    preferred_study_time: Optional[str] = None
    timezone: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8)


# =============================================================================
# Response Schemas
# =============================================================================

class UserResponse(UserBase):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    daily_review_goal: int
    preferred_study_time: Optional[str]
    timezone: str


class TokenResponse(BaseModel):
    """Schema for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: int  # user_id
    exp: Optional[datetime] = None
    type: str = "access"  # access or refresh


class UserStats(BaseModel):
    """Schema for user statistics."""
    total_entries: int
    completed_entries: int
    total_patterns: int
    total_reviews: int
    current_streak: int
    reviews_today: int
    reviews_due_today: int
