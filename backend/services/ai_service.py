"""
AI Service for Thinking OS.

WHY: Natural language understanding transforms the learning capture experience.
Instead of filling forms, users describe their experience conversationally,
and AI extracts structured reflection data. This removes friction while
maintaining the rigor of structured reflection.

Built with LangChain + Gemini 2.5 Flash for reliable structured output.
"""

import json
from typing import Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from config import settings


class ExtractedLearning(BaseModel):
    """Structured learning data extracted from natural language."""
    entry_type: str = Field(description="One of: dsa, backend, ai_ml, debug, interview, concept, project")
    title: str = Field(description="Concise title (5-10 words) summarizing what was learned")
    context: str = Field(description="What were they trying to accomplish? (2-3 sentences)")
    initial_blocker: str = Field(description="What specifically blocked them? Where did they get stuck?")
    trigger_signal: str = Field(description="The 'aha' moment - what made it click?")
    key_pattern: str = Field(description="Reusable insight/pattern for next time (actionable)")
    mistake_or_edge_case: str = Field(description="What to watch out for next time")
    suggested_patterns: list[str] = Field(description="2-4 short pattern tags")
    time_spent_minutes: int = Field(description="Estimated time in minutes")
    difficulty: int = Field(description="Rating 1-5 (1=trivial, 5=very hard)")


class AIService:
    """
    Service for AI-powered analysis of learning experiences.
    
    WHY: Gemini 2.5 Flash excels at extracting structured data from natural language.
    LangChain provides reliable structured output parsing and prompt management.
    """
    
    def __init__(self):
        if settings.GEMINI_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-preview-05-20",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.3,  # Lower for more consistent extraction
            )
            self.parser = JsonOutputParser(pydantic_object=ExtractedLearning)
            self.chain = self._build_chain()
        else:
            self.llm = None
            self.chain = None
    
    @property
    def model(self):
        """Backward compatibility - check if AI is configured."""
        return self.llm
    
    def _build_chain(self):
        """Build the LangChain extraction chain."""
        
        system_prompt = """You are an expert at analyzing learning experiences and extracting structured reflection data.

A developer is describing a problem-solving or learning experience. Extract the following information:

1. **entry_type**: One of: dsa, backend, ai_ml, debug, interview, concept, project
   - dsa: Data structures, algorithms, leetcode-style problems
   - backend: APIs, databases, servers, system design
   - ai_ml: Machine learning, AI, data science
   - debug: Debugging sessions, fixing bugs
   - interview: Interview prep, mock interviews
   - concept: Learning new concepts, theory
   - project: Project work, feature implementation

2. **title**: A concise title (5-10 words) summarizing what was learned/solved

3. **context**: What were they trying to accomplish? What was the goal? (2-3 sentences)

4. **initial_blocker**: What specifically blocked them? Where did they get stuck? (Be specific)

5. **trigger_signal**: What was the "aha" moment? What made it click? What helped them break through?

6. **key_pattern**: What's the reusable insight/pattern they can apply next time? (This is the gold - make it actionable)

7. **mistake_or_edge_case**: What should they watch out for next time? Any gotchas or edge cases?

8. **suggested_patterns**: List of 2-4 short pattern tags (e.g., "two-pointer", "edge-case-check", "read-error-message")

9. **time_spent_minutes**: Estimated time spent (number only, in minutes). If not mentioned, estimate based on complexity.

10. **difficulty**: Rate 1-5 (1=trivial, 5=very hard)

{format_instructions}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{raw_input}")
        ])
        
        return prompt | self.llm | self.parser
    
    def analyze_experience(self, raw_input: str) -> dict:
        """
        Analyze a natural language description of a learning experience.
        
        WHY: Users describe what happened in their own words. This method
        extracts all the structured fields we need for meaningful reflection.
        
        Args:
            raw_input: User's natural description of their experience
            
        Returns:
            Dictionary with extracted fields ready for entry creation
        """
        if not self.chain:
            raise ValueError("Gemini API key not configured. Set GEMINI_API_KEY in .env")
        
        try:
            result = self.chain.invoke({
                "raw_input": raw_input,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            result = self._normalize_result(result)
            return result
            
        except Exception as e:
            raise ValueError(f"AI analysis failed: {str(e)}")
    
    def _normalize_result(self, data: dict) -> dict:
        """Normalize and validate extracted data."""
        
        valid_types = ['dsa', 'backend', 'ai_ml', 'debug', 'interview', 'concept', 'project']
        if data.get('entry_type') not in valid_types:
            type_mapping = {
                'algorithm': 'dsa',
                'algorithms': 'dsa',
                'data_structure': 'dsa',
                'api': 'backend',
                'database': 'backend',
                'ml': 'ai_ml',
                'machine_learning': 'ai_ml',
                'bug': 'debug',
                'debugging': 'debug',
            }
            data['entry_type'] = type_mapping.get(
                data.get('entry_type', '').lower(), 
                'concept'
            )
        
        data.setdefault('suggested_patterns', [])
        data.setdefault('time_spent_minutes', 30)
        data.setdefault('difficulty', 3)
        
        if isinstance(data.get('suggested_patterns'), str):
            data['suggested_patterns'] = [p.strip() for p in data['suggested_patterns'].split(',')]
        
        return data


_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create the AI service singleton."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
