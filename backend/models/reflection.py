"""
Reflection model - the mandatory thinking capture.

WHY: This is the heart of Thinking OS. Every entry MUST have
a reflection to be saved. The reflection captures the metacognitive
process - not what you learned, but HOW you learned it.

PHILOSOPHY: Most note-taking systems capture the solution.
Thinking OS captures the thinking that led to the solution.
This makes knowledge transferable and patterns discoverable.
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, 
    ForeignKey
)
from sqlalchemy.orm import relationship

from database import Base


class Reflection(Base):
    """
    Mandatory reflection for each entry.
    
    WHY each field (these are NON-NEGOTIABLE):
    
    - context: What was I trying to solve/build?
      Sets the stage. Without context, the learning is orphaned.
      
    - initial_blocker: Why was I stuck or unsure?
      This is WHERE the learning happens. The gap between
      what you knew and what you needed to know.
      
    - trigger_signal: What revealed the correct direction?
      The "aha moment" - a hint, an error message, a pattern.
      THIS is what you want to recognize faster next time.
      
    - key_pattern: Name it in YOUR words.
      User-defined pattern name. Not textbook terms, but
      how YOU think about it. This builds personal vocabulary.
      
    - mistake_or_edge_case: One thing to remember.
      The specific gotcha, edge case, or mistake. These are
      gold for interview prep and future debugging.
      
    - time_to_insight_minutes: How long until breakthrough?
      Track your insight speed over time.
    """
    __tablename__ = "reflections"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=False, unique=True)
    
    # MANDATORY FIELDS - Core reflection
    context = Column(Text, nullable=False)
    initial_blocker = Column(Text, nullable=False)
    trigger_signal = Column(Text, nullable=False)
    key_pattern = Column(String(500), nullable=False, index=True)
    mistake_or_edge_case = Column(Text, nullable=False)
    
    # Optional but valuable
    time_to_insight_minutes = Column(Integer, nullable=True)
    
    # Additional notes (free-form, for anything else)
    additional_notes = Column(Text, nullable=True)
    
    # What would you do differently?
    # WHY: Forces forward-thinking, not just retrospection
    next_time_strategy = Column(Text, nullable=True)
    
    # Self-rated confidence (1-5)
    # WHY: Track how confident you feel about this pattern
    confidence_level = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship back to entry
    entry = relationship("Entry", back_populates="reflection")
    
    def __repr__(self):
        return f"<Reflection(id={self.id}, pattern='{self.key_pattern}')>"
    
    def is_complete(self) -> bool:
        """
        Validate that all mandatory fields are filled.
        
        WHY: Programmatic enforcement of reflection requirement.
        This is called before persisting to ensure quality.
        """
        mandatory_fields = [
            self.context,
            self.initial_blocker,
            self.trigger_signal,
            self.key_pattern,
            self.mistake_or_edge_case
        ]
        return all(
            field is not None and str(field).strip() != ""
            for field in mandatory_fields
        )
