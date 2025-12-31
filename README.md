# NeurOS

> A personal knowledge system that captures **thinking patterns**, not just solutions.

## Philosophy

Most note-taking systems capture what you learned. Thinking OS captures **how** you learned it.

- **No reflection → No persistence**: Every entry requires mandatory reflection
- **Patterns over notes**: Build a vocabulary of reusable thinking patterns
- **Past struggles as teachers**: The recall system surfaces relevant history
- **Data-driven improvement**: Track blockers, strengths, and weaknesses

## Quick Start

### Backend Setup

```bash
cd NeurOS/backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

Backend runs at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### Frontend Setup

```bash
cd NeurOS/frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs at `http://localhost:3000`

## Core Concepts

### Entries
Learning moments across domains:
- **DSA / CP**: Algorithm problems, competitive programming
- **Backend**: FastAPI, APIs, system design
- **AI / ML**: Machine learning, GenAI experiments
- **Debug**: Bug fixes, debugging sessions
- **Interview**: Interview questions, mock sessions
- **Concept**: Pure learning, theory understanding
- **Project**: Project-based learning

### Mandatory Reflection
Every entry requires:
1. **Context**: What were you trying to solve/build?
2. **Initial Blocker**: Why were you stuck or unsure?
3. **Trigger Signal**: What revealed the correct direction?
4. **Key Pattern**: Name it in YOUR words
5. **Mistake/Edge Case**: One thing to remember

### Patterns
User-defined thinking patterns:
- Cross-domain patterns (most valuable)
- Usage tracking and success rates
- Common triggers and mistakes

### Recall System
Before starting new work:
- Find similar past entries
- Get relevant pattern suggestions
- See blocker warnings ("you struggled with X 3 times")
- Get revision recommendations

## API Overview

```
POST /api/v1/entries                    # Create entry
POST /api/v1/entries/{id}/reflection    # Add reflection (completes entry)
GET  /api/v1/entries                    # List entries

GET  /api/v1/patterns                   # List patterns
POST /api/v1/patterns                   # Create pattern

POST /api/v1/recall/context             # Get full recall before new work

GET  /api/v1/analytics/insights         # Get progress insights
GET  /api/v1/analytics/revision-queue   # Get items due for revision
```

## Project Structure

```
NeurOS/
├── backend/
│   ├── main.py                      # FastAPI application
│   ├── config.py                    # Configuration
│   ├── database.py                  # SQLite setup
│   ├── requirements.txt             # Python dependencies
│   ├── data/                        # Database files
│   ├── models/                      # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── analytics.py
│   │   ├── entry.py
│   │   ├── learning_plan.py
│   │   ├── pattern.py
│   │   ├── recommendation.py
│   │   └── reflection.py
│   ├── schemas/                     # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── analytics.py
│   │   ├── entry.py
│   │   ├── learning_plan.py
│   │   ├── pattern.py
│   │   ├── recommendation.py
│   │   └── reflection.py
│   ├── services/                    # Business logic
│   │   ├── __init__.py
│   │   ├── ai_service.py
│   │   ├── analytics_service.py
│   │   ├── entry_service.py
│   │   ├── pattern_service.py
│   │   ├── plan_service.py
│   │   ├── recall_service.py
│   │   └── recommendation_service.py
│   └── routes/                      # API endpoints
│       ├── __init__.py
│       ├── ai.py
│       ├── analytics.py
│       ├── entries.py
│       ├── patterns.py
│       ├── plans.py
│       ├── recall.py
│       └── recommendations.py
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── tsconfig.json
    ├── tsconfig.node.json
    ├── public/
    └── src/
        ├── App.tsx
        ├── main.tsx
        ├── index.css
        ├── vite-env.d.ts
        ├── components/              # Reusable components
        │   ├── EntryCard.tsx
        │   ├── EntryTypeBadge.tsx
        │   ├── Layout.tsx
        │   └── ReflectionForm.tsx
        ├── lib/                     # API client, types
        │   ├── api.ts
        │   └── types.ts
        └── pages/                   # React pages
            ├── Analytics.tsx
            ├── Dashboard.tsx
            ├── EntryDetail.tsx
            ├── NewEntry.tsx
            ├── Patterns.tsx
            ├── Plans.tsx
            ├── Recall.tsx
            ├── Recommendations.tsx
            └── Revision.tsx
```

## Future Extensions

The codebase is designed for future enhancements:

### Embedding-Based Search
```python
# In models/entry.py
embedding = Column(Text, nullable=True)  # Ready for vector storage
```

### LLM Integration
```python
# In config.py
EMBEDDING_MODEL: Optional[str] = None  # e.g., "text-embedding-ada-002"
LLM_MODEL: Optional[str] = None        # e.g., "gpt-4"
```

### Multi-User Support
- Current: Single-user with simple token auth
- Future: Add user model, OAuth, team features

## Usage Tips

1. **Always reflect**: Don't just log solutions, capture your thinking
2. **Name patterns YOUR way**: "pointer dance" > "two pointers" if that's how you think
3. **Check recall before starting**: Use the recall system to leverage past experience
4. **Regular revision**: Visit the revision page to strengthen memory
5. **Track blockers**: Pay attention to repeated blockers - they reveal systematic gaps

---

Built for daily use over years. Optimize for clarity, recall, and long-term leverage.
