# NeurOS 2.0

> **Metacognitive Learning & Retention System** - A personal knowledge system that captures **thinking patterns**, tracks **memory decay**, and optimizes **long-term retention** through spaced repetition.

## 🧠 Philosophy

Most note-taking systems capture what you learned. NeurOS captures **how** you learned it and ensures you **remember** it.

- **No reflection → No persistence**: Every entry requires mandatory reflection
- **Patterns over notes**: Build a vocabulary of reusable thinking patterns  
- **Retention over recall**: Active spaced repetition with SuperMemo-2 algorithm
- **Decay tracking**: Ebbinghaus forgetting curve visualization
- **Knowledge graph**: Connect concepts to see the bigger picture
- **Flash coding**: Practice with code templates
- **Daily intelligence**: Morning standup with personalized priorities

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone and start all services
cd NeurOS
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend

```bash
cd NeurOS/backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r app/requirements.txt

# Set environment variables
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/neuros
export JWT_SECRET_KEY=your-secret-key

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd NeurOS/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## ✨ Key Features

### 1. Spaced Repetition System (SRS)
- **SuperMemo-2 algorithm** for optimal review scheduling
- **Quality-based ratings** (1-5) adjust intervals dynamically
- **Due items** prioritized in daily review queue
- **Suspension/bury** for temporary exclusion

### 2. Decay Tracking
- **Ebbinghaus forgetting curve** visualization
- **Critical alerts** when retention drops below threshold
- **Practice heatmap** showing activity patterns
- **Strength tracking** across all knowledge items

### 3. Knowledge Graph
- **D3.js visualization** of concept connections
- **Node types**: concepts, techniques, patterns, algorithms
- **Relationship types**: prerequisites, related, contrast, examples
- **Mastery levels** (1-5) shown by node size

### 4. Flash Coding
- **Monaco Editor** integration for code practice
- **Pattern templates** with solutions hidden
- **Quality self-rating** after each attempt
- **Language support**: Python, JS, TS, Rust, Go, and more

### 5. Daily Intelligence
- **Morning standup** with personalized recommendations
- **Priority stack**: urgent reviews, decaying items, new material
- **Time-aware greetings** and motivational messaging
- **Progress tracking** toward daily goals

## 📚 Core Concepts

### Entries
Learning moments across domains:
- **Concept**: Core ideas, theory, mental models
- **Problem**: DSA, competitive programming, exercises
- **Project**: Project-based learning, builds
- **Debug**: Bug fixes, troubleshooting sessions
- **Insight**: Aha moments, realizations
- **Question**: Open questions, research topics

### Mandatory Reflection
Every entry requires 5 reflection fields:
1. **What I learned**: Core takeaway
2. **What was confusing**: Initial blockers
3. **What to explore next**: Future directions
4. **Confidence level**: Self-assessment (1-5)
5. **Key pattern**: Named in YOUR words

### Patterns
User-defined thinking patterns:
- Cross-domain patterns (most valuable)
- Usage tracking and success rates
- Code templates for practice

### Review Queue
Before starting new work:
- See items due for review
- Track streak and completion
- Quality ratings update scheduling

## 🏗 Architecture

```
NeurOS/
├── backend/
│   └── app/
│       ├── api/v1/endpoints/    # FastAPI routes
│       ├── core/                # Algorithms (SRS, decay)
│       ├── models/              # SQLAlchemy models
│       ├── schemas/             # Pydantic schemas
│       └── services/            # Business logic
├── frontend/
│   └── src/
│       ├── components/          # React components
│       ├── pages/               # Route pages
│       ├── lib/                 # API client, types
│       └── stores/              # Zustand stores
└── docker-compose.yml           # Full stack deployment
```

### Tech Stack

**Backend:**
- FastAPI + Python 3.11
- PostgreSQL + SQLAlchemy 2.0 (async)
- Alembic migrations
- Celery + Redis for background tasks
- JWT authentication

**Frontend:**
- React 18 + TypeScript
- TanStack Query for server state
- Zustand for client state
- D3.js for knowledge graph
- Monaco Editor for code
- Tailwind CSS

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Create account |
| `/api/v1/auth/login` | POST | Get tokens |
| `/api/v1/entries` | GET/POST | List/create entries |
| `/api/v1/patterns` | GET/POST | List/create patterns |
| `/api/v1/reviews/queue` | GET | Get review queue |
| `/api/v1/reviews/{id}/submit` | POST | Submit review |
| `/api/v1/decay/overview` | GET | Decay statistics |
| `/api/v1/standup/today` | GET | Daily plan |
| `/api/v1/graph` | GET | Knowledge graph |
| `/api/v1/analytics/dashboard` | GET | Analytics data |

## 🔧 Environment Variables

```env
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/neuros
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend
VITE_API_URL=http://localhost:8000
```

## 📈 Roadmap

- [ ] AI-powered pattern extraction
- [ ] Collaborative knowledge sharing
- [ ] Mobile app (React Native)
- [ ] Browser extension for quick capture
- [ ] Obsidian/Notion integration
- [ ] Export to Anki format

## 📝 License

MIT License - See LICENSE file for details.

---

**Remember**: Patterns over notes. Retention over recall. 🧠
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
