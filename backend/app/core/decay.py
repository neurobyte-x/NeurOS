"""
NeurOS 2.0 Decay Calculation System

Implementation of knowledge decay based on the Ebbinghaus Forgetting Curve.

SCIENTIFIC BASIS:
The forgetting curve shows that memory retention decays exponentially over time.
Without review, approximately 56% of information is forgotten within an hour,
and 66% within a day.

FORMULA:
R = e^(-t/S)

Where:
- R = retention (0-1)
- t = time elapsed
- S = stability (strength of memory)

We modify this to account for:
1. Number of reviews (more reviews = slower decay)
2. Initial difficulty (harder items decay faster)
3. Quality of recall (better recall = stronger memory)
"""

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.config import settings


class DecayStatus(Enum):
    """Visual status indicators for decay levels."""
    FRESH = "fresh"           # 80-100: Recently reviewed, strong memory
    STABLE = "stable"         # 60-79: Good retention, review soon
    DECAYING = "decaying"     # 40-59: Starting to forget, needs review
    CRITICAL = "critical"     # 20-39: Significant forgetting, urgent review
    FORGOTTEN = "forgotten"   # 0-19: Likely forgotten, needs relearning


@dataclass
class DecayResult:
    """Result of decay calculation."""
    decay_score: int  # 0-100
    status: DecayStatus
    days_until_critical: Optional[int]
    recommended_review_date: datetime
    stability_factor: float


class DecayEngine:
    """
    Knowledge decay calculation engine.
    
    Uses modified Ebbinghaus forgetting curve with personalization
    based on review history and item characteristics.
    """
    
    # Base half-life in days (time for decay to reach 50%)
    BASE_HALF_LIFE = settings.DECAY_HALF_LIFE_DAYS
    
    # Stability multipliers
    REVIEW_STABILITY_BONUS = 0.3  # Each review adds 30% to stability
    MAX_STABILITY_MULTIPLIER = 5.0  # Cap stability growth
    
    @staticmethod
    def calculate_decay_score(
        last_practiced_at: datetime,
        times_reviewed: int = 0,
        initial_difficulty: int = 50,  # 1-100, higher = harder
        last_quality: int = 4,  # Last recall quality (0-5)
        current_time: Optional[datetime] = None,
    ) -> DecayResult:
        """
        Calculate the current decay score for a knowledge item.
        
        Args:
            last_practiced_at: When the item was last reviewed
            times_reviewed: Total number of reviews
            initial_difficulty: Item difficulty (1-100)
            last_quality: Quality of last recall (0-5)
            current_time: Optional current time (for testing)
            
        Returns:
            DecayResult with score, status, and recommendations
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        # Ensure timezone awareness
        if last_practiced_at.tzinfo is None:
            last_practiced_at = last_practiced_at.replace(tzinfo=timezone.utc)
        
        # Calculate time elapsed in days
        time_elapsed = (current_time - last_practiced_at).total_seconds() / 86400
        
        # Calculate stability factor
        stability = DecayEngine._calculate_stability(
            times_reviewed, initial_difficulty, last_quality
        )
        
        # Calculate retention using modified forgetting curve
        # R = e^(-t/S) where t is time and S is stability
        half_life = DecayEngine.BASE_HALF_LIFE * stability
        retention = math.exp(-time_elapsed / half_life * math.log(2))
        
        # Convert to 0-100 score
        decay_score = int(retention * 100)
        decay_score = max(0, min(100, decay_score))
        
        # Determine status
        status = DecayEngine._get_status(decay_score)
        
        # Calculate days until critical
        days_until_critical = DecayEngine._days_until_threshold(
            decay_score, 
            settings.DECAY_CRITICAL_THRESHOLD,
            half_life
        )
        
        # Recommend review date (aim to review before hitting warning threshold)
        days_until_warning = DecayEngine._days_until_threshold(
            decay_score,
            settings.DECAY_WARNING_THRESHOLD,
            half_life
        )
        
        if days_until_warning is not None and days_until_warning > 0:
            recommended_review = current_time + \
                datetime.timedelta(days=max(1, days_until_warning - 1))
        else:
            # Already at or below warning, review now
            recommended_review = current_time
        
        return DecayResult(
            decay_score=decay_score,
            status=status,
            days_until_critical=days_until_critical,
            recommended_review_date=recommended_review,
            stability_factor=stability,
        )
    
    @staticmethod
    def _calculate_stability(
        times_reviewed: int,
        initial_difficulty: int,
        last_quality: int,
    ) -> float:
        """
        Calculate memory stability factor.
        
        Higher stability = slower decay.
        """
        # Base stability
        stability = 1.0
        
        # Review bonus (diminishing returns)
        review_bonus = sum(
            DecayEngine.REVIEW_STABILITY_BONUS * (0.8 ** i)
            for i in range(times_reviewed)
        )
        stability += review_bonus
        
        # Difficulty modifier (harder items have lower stability)
        difficulty_modifier = 1.0 - (initial_difficulty / 200)  # 0.5 to 1.0
        stability *= difficulty_modifier
        
        # Quality modifier (better recall = higher stability)
        quality_modifier = 0.7 + (last_quality / 5 * 0.6)  # 0.7 to 1.3
        stability *= quality_modifier
        
        # Cap stability
        return min(stability, DecayEngine.MAX_STABILITY_MULTIPLIER)
    
    @staticmethod
    def _get_status(decay_score: int) -> DecayStatus:
        """Get decay status from score."""
        if decay_score >= 80:
            return DecayStatus.FRESH
        elif decay_score >= 60:
            return DecayStatus.STABLE
        elif decay_score >= 40:
            return DecayStatus.DECAYING
        elif decay_score >= 20:
            return DecayStatus.CRITICAL
        else:
            return DecayStatus.FORGOTTEN
    
    @staticmethod
    def _days_until_threshold(
        current_score: int,
        threshold: int,
        half_life: float,
    ) -> Optional[int]:
        """
        Calculate days until decay score reaches threshold.
        
        Returns None if already at or below threshold.
        """
        if current_score <= threshold:
            return None
        
        # R = e^(-t/h * ln(2))
        # Solve for t: t = -h * ln(R) / ln(2)
        current_retention = current_score / 100
        target_retention = threshold / 100
        
        # Days to go from current to target
        days = -half_life * math.log(target_retention / current_retention) / math.log(2)
        
        return max(0, int(days))
    
    @staticmethod
    def batch_calculate(
        items: list[dict],
        current_time: Optional[datetime] = None,
    ) -> list[DecayResult]:
        """
        Calculate decay for multiple items efficiently.
        
        Args:
            items: List of dicts with keys: last_practiced_at, times_reviewed,
                   initial_difficulty, last_quality
                   
        Returns:
            List of DecayResult in same order as input
        """
        results = []
        for item in items:
            result = DecayEngine.calculate_decay_score(
                last_practiced_at=item.get("last_practiced_at"),
                times_reviewed=item.get("times_reviewed", 0),
                initial_difficulty=item.get("initial_difficulty", 50),
                last_quality=item.get("last_quality", 4),
                current_time=current_time,
            )
            results.append(result)
        return results


def calculate_decay(
    last_practiced_at: datetime,
    times_reviewed: int = 0,
    initial_difficulty: int = 50,
    last_quality: int = 4,
) -> int:
    """
    Convenience function for decay calculation.
    
    Returns:
        Decay score (0-100)
    """
    result = DecayEngine.calculate_decay_score(
        last_practiced_at=last_practiced_at,
        times_reviewed=times_reviewed,
        initial_difficulty=initial_difficulty,
        last_quality=last_quality,
    )
    return result.decay_score


def get_decay_status(decay_score: int) -> str:
    """Get string status from decay score."""
    return DecayEngine._get_status(decay_score).value
