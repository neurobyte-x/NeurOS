"""
NeurOS 2.0 Spaced Repetition System (SRS)

Implementation of SuperMemo-2 algorithm for optimal review scheduling.

ALGORITHM OVERVIEW:
The SuperMemo-2 algorithm schedules reviews based on:
1. Quality of recall (0-5 rating)
2. Current interval (days since last review)
3. Ease factor (item difficulty modifier)

Key formula:
- EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
- Where EF' is new ease factor, EF is current, q is quality (0-5)

Reference: https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-supermemo-method
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from typing import Optional

from app.config import settings


class RecallQuality(IntEnum):
    """
    Quality ratings for recall assessment.
    
    0-2: Failure (item needs to be relearned)
    3-5: Success (item was recalled with varying ease)
    """
    BLACKOUT = 0       # Complete failure, no memory
    INCORRECT = 1      # Incorrect, but upon seeing answer felt familiar
    HARD_INCORRECT = 2 # Incorrect, but remembered after hint
    HARD_CORRECT = 3   # Correct, but with significant difficulty
    GOOD = 4           # Correct, with some hesitation
    PERFECT = 5        # Perfect recall, immediate response


@dataclass
class SRSResult:
    """Result of an SRS calculation."""
    next_interval_days: int
    new_ease_factor: float
    next_review_date: datetime
    is_graduated: bool  # Has passed initial learning phase
    repetition_number: int


class SRSEngine:
    """
    SuperMemo-2 based spaced repetition engine.
    
    Features:
    - Adaptive intervals based on recall quality
    - Ease factor adjustment per item
    - Graduation system (learning -> review)
    - Lapse handling (when forgotten)
    """
    
    # Initial learning intervals (in days)
    LEARNING_STEPS = [0, 1, 3]  # Same day, 1 day, 3 days
    
    # Minimum and maximum intervals
    MIN_INTERVAL = 1
    MAX_INTERVAL = 365
    
    @staticmethod
    def calculate_next_review(
        quality: int,
        current_interval: int,
        ease_factor: float,
        repetition_number: int = 0,
        is_graduated: bool = False,
    ) -> SRSResult:
        """
        Calculate the next review date and parameters.
        
        Args:
            quality: Recall quality rating (0-5)
            current_interval: Current interval in days
            ease_factor: Current ease factor (default 2.5)
            repetition_number: Number of successful repetitions
            is_graduated: Whether item has passed learning phase
            
        Returns:
            SRSResult with next interval, ease factor, and review date
        """
        quality = max(0, min(5, quality))  # Clamp to 0-5
        
        # Ensure minimum ease factor
        ease_factor = max(settings.SRS_MINIMUM_EASE_FACTOR, ease_factor)
        
        # Handle failed recall (quality < 3)
        if quality < 3:
            return SRSEngine._handle_lapse(
                quality, ease_factor, repetition_number
            )
        
        # Handle successful recall
        return SRSEngine._handle_success(
            quality, current_interval, ease_factor, 
            repetition_number, is_graduated
        )
    
    @staticmethod
    def _handle_lapse(
        quality: int,
        ease_factor: float,
        repetition_number: int,
    ) -> SRSResult:
        """
        Handle a failed recall (lapse).
        
        Reset to learning phase with reduced ease factor.
        """
        # Reduce ease factor (but not below minimum)
        new_ease_factor = max(
            settings.SRS_MINIMUM_EASE_FACTOR,
            ease_factor - 0.2
        )
        
        # Reset to first learning step
        next_interval = SRSEngine.LEARNING_STEPS[0]
        if next_interval == 0:
            next_interval = 1  # Minimum 1 day
        
        return SRSResult(
            next_interval_days=next_interval,
            new_ease_factor=new_ease_factor,
            next_review_date=datetime.now(timezone.utc) + timedelta(days=next_interval),
            is_graduated=False,  # Back to learning phase
            repetition_number=0,  # Reset repetition count
        )
    
    @staticmethod
    def _handle_success(
        quality: int,
        current_interval: int,
        ease_factor: float,
        repetition_number: int,
        is_graduated: bool,
    ) -> SRSResult:
        """
        Handle a successful recall.
        
        Calculate new interval using SuperMemo-2 formula.
        """
        # Update ease factor using SM-2 formula
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ease_factor = ease_factor + (
            0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        )
        new_ease_factor = max(settings.SRS_MINIMUM_EASE_FACTOR, new_ease_factor)
        
        # Calculate next interval
        if not is_graduated:
            # Still in learning phase
            if repetition_number < len(SRSEngine.LEARNING_STEPS) - 1:
                next_interval = SRSEngine.LEARNING_STEPS[repetition_number + 1]
                graduated = False
            else:
                # Graduate to review phase
                next_interval = settings.SRS_INITIAL_INTERVAL_DAYS
                graduated = True
        else:
            # In review phase - apply ease factor
            if repetition_number == 0:
                next_interval = settings.SRS_INITIAL_INTERVAL_DAYS
            elif repetition_number == 1:
                next_interval = 6
            else:
                next_interval = int(current_interval * new_ease_factor)
            graduated = True
        
        # Clamp interval
        next_interval = max(SRSEngine.MIN_INTERVAL, 
                          min(SRSEngine.MAX_INTERVAL, next_interval))
        
        return SRSResult(
            next_interval_days=next_interval,
            new_ease_factor=new_ease_factor,
            next_review_date=datetime.now(timezone.utc) + timedelta(days=next_interval),
            is_graduated=graduated,
            repetition_number=repetition_number + 1,
        )
    
    @staticmethod
    def get_priority_score(
        next_review_date: datetime,
        decay_score: int,
        ease_factor: float,
    ) -> float:
        """
        Calculate priority score for review queue ordering.
        
        Higher score = higher priority.
        
        Factors:
        - Overdue items get highest priority
        - Low decay score increases priority
        - Lower ease factor (harder items) get slight boost
        """
        now = datetime.now(timezone.utc)
        
        # Days overdue (negative if not yet due)
        if next_review_date.tzinfo is None:
            next_review_date = next_review_date.replace(tzinfo=timezone.utc)
        
        days_overdue = (now - next_review_date).days
        
        # Base score from overdue status
        overdue_score = max(0, days_overdue) * 10
        
        # Decay contribution (higher decay = lower score, invert it)
        decay_contribution = (100 - decay_score) * 0.5
        
        # Difficulty contribution (harder items slightly prioritized)
        difficulty_contribution = (3.0 - ease_factor) * 5
        
        return overdue_score + decay_contribution + difficulty_contribution


def calculate_srs(
    quality: int,
    current_interval: int = 1,
    ease_factor: float = 2.5,
    repetition_number: int = 0,
    is_graduated: bool = False,
) -> tuple[int, float, datetime]:
    """
    Convenience function for SRS calculation.
    
    Returns:
        Tuple of (next_interval_days, new_ease_factor, next_review_date)
    """
    result = SRSEngine.calculate_next_review(
        quality=quality,
        current_interval=current_interval,
        ease_factor=ease_factor,
        repetition_number=repetition_number,
        is_graduated=is_graduated,
    )
    return (
        result.next_interval_days,
        result.new_ease_factor,
        result.next_review_date,
    )
