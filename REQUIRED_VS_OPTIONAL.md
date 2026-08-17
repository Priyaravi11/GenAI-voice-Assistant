# REQUIRED vs OPTIONAL COMPONENTS GUIDE

## Overview

This document clarifies what components are **REQUIRED** for the system to run vs. what components are **OPTIONAL** for enhanced features.

---

## REQUIRED COMPONENTS

### Must Have for Basic Functionality

#### 1. **Backend Core**
- ✅ Python 3.11+
- ✅ FastAPI framework
- ✅ Uvicorn ASGI server
- ✅ Pydantic models
- ✅ python-dotenv

**Why:** FastAPI serves the API and WebSocket endpoints. Without this, there's no backend.

**Installation:**
```bash
pip install fastapi uvicorn pydantic python-dotenv
```

**Start:**
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

---

#### 2. **Frontend Core**
- ✅ Node.js 20+
- ✅ React 19+
- ✅ Vite
- ✅ TypeScript

**Why:** React/Vite is the UI layer for user interaction.

**Installation:**
```bash
cd frontend
npm install
```

**Start:**
```bash
npm run dev
```

---

#### 3. **Gemini API Integration**
- ✅ google-genai package
- ✅ Valid GEMINI_API_KEY from Google Cloud

**Why:** Gemini is the core AI engine for responses.

**Get API Key:**
1. Go to https://aistudio.google.com/
2. Create new API key
3. Add to `.env`: `GEMINI_API_KEY=your_key_here`

**Installation:**
```bash
pip install google-genai
```

---

#### 4. **RAG System (ChromaDB)**
- ✅ chromadb package
- ✅ sentence-transformers (embeddings)
- ✅ Knowledge base documents (in rag/data/)

**Why:** ChromaDB provides knowledge retrieval for customer questions.

**Installation:**
```bash
pip install chromadb sentence-transformers
```

**Data Location:**
```
rag/data/chroma/  ← Vector database
rag/data/raw/knowledge_base/  ← Raw documents
```

**Works Without:** The system gracefully handles missing data and will use Gemini alone for responses.

---

#### 5. **Telecom Tools**
- ✅ billing_tool.py
- ✅ payment_tool.py
- ✅ plans_tool.py
- ✅ network_tool.py
- ✅ customer_tool.py

**Why:** Tools provide customer-specific data (bills, payments, plans, etc.).

**Location:** `tools/*.py` (already implemented)

**Works Without:** Tools can return mock data or be stubbed. The system doesn't crash if a tool fails.

---

#### 6. **WebSocket Support**
- ✅ websockets package (in requirements.txt)
- ✅ CORS enabled in FastAPI

**Why:** WebSocket enables real-time communication between frontend and backend.

**Already Included:** Yes, in requirements.txt

---

#### 7. **Environment Configuration**
- ✅ .env file with GEMINI_API_KEY

**Minimum .env:**
```bash
GEMINI_API_KEY=your_key_here
MONGODB_URI=mongodb://localhost:27017/genai_assistant
MONGODB_DATABASE=genai_assistant
ENVIRONMENT=development
```

**Works Without MongoDB:** Yes, graceful fallback. Tools return mock data.

---

## OPTIONAL COMPONENTS

### Nice to Have but Not Required

#### 1. **MongoDB** ⚠️ OPTIONAL
- Stores customer data, call history
- Provides tool data (bills, payments, etc.)

**Impact Without:**
- ✅ System still works
- ⚠️ Tools return mock/dummy data
- ⚠️ No persistent customer information

**Setup (if you want it):**
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Using local MongoDB
mongod
```

**Configure in .env:**
```bash
MONGODB_URI=mongodb://localhost:27017/genai_assistant
```

---

#### 2. **JWT Authentication** ⚠️ OPTIONAL
- Secures API endpoints
- User session management

**Current Status:** Not implemented (anyone can call the API)

**Impact Without:**
- ✅ System works
- ⚠️ No user authentication
- ⚠️ Anyone can call endpoints

**To Add Later:**
```python
# Would require
pip install python-jose cryptography
```

---

#### 3. **Redis Caching** ⚠️ OPTIONAL
- Caches session data
- Improves response time

**Current Status:** Not implemented (uses in-memory storage)

**Impact Without:**
- ✅ System works
- ⚠️ No caching (session info stored in memory)
- ⚠️ Loses sessions if backend restarts

**To Add Later:**
```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Using local Redis
redis-server
```

---

#### 4. **Application Monitoring** ⚠️ OPTIONAL
- Prometheus metrics
- OpenTelemetry tracing
- Logs aggregation

**Current Status:** Basic logging only (no external monitoring)

**Impact Without:**
- ✅ System works
- ⚠️ No performance metrics
- ⚠️ Harder to debug issues

**To Add Later:**
```python
pip install prometheus-client opentelemetry-api
```

---

#### 5. **Docker Containerization** ⚠️ OPTIONAL
- Containerizes backend and frontend
- Simplifies deployment

**Current Status:** Not created

**Impact Without:**
- ✅ System works perfectly
- ⚠️ Must manually manage dependencies
- ⚠️ May have OS-specific issues

**To Skip Docker:** Just follow the manual setup (see section below)

---

#### 6. **Database Seeding Scripts** ⚠️ OPTIONAL
- Pre-populates MongoDB with test data
- Saves time for development

**Current Status:** Script exists but not required
- Location: `scripts/seed_mongodb.py`

**Impact Without:**
- ✅ System works
- ⚠️ Tools return mock/empty data
- ⚠️ No test scenarios to play with

**To Seed (Optional):**
```bash
python scripts/seed_mongodb.py
```

---

## WHAT YOU NEED TO RUN

### Absolute Minimum (Text Mode Only)
```
✅ Python 3.11+
✅ Node.js 20+
✅ GEMINI_API_KEY
✅ FastAPI + Uvicorn
✅ React + Vite
✅ ChromaDB + sentence-transformers
```

### For Audio Mode (Gemini Live)
```
✅ Everything above, PLUS:
✅ Web Audio API support (modern browsers only)
✅ Microphone access permission
```

### For Full Features
```
✅ Everything above, PLUS:
⚠️ MongoDB (optional but recommended)
⚠️ Redis (optional)
⚠️ JWT authentication setup (optional)
```

---

## QUICK START (WITHOUT OPTIONAL COMPONENTS)

### Step 1: Setup Backend
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install required packages
pip install -r backend/requirements.txt

# Configure .env
cp .env.example .env
# Edit .env and add GEMINI_API_KEY
```

### Step 2: Setup Frontend
```bash
cd frontend
npm install
```

### Step 3: Start Backend
```bash
# Terminal 1
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 4: Start Frontend
```bash
# Terminal 2
cd frontend
npm run dev
```

### Step 5: Access
```
Frontend: http://localhost:5173
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
```

**That's it!** The system will work with:
- ✅ Text-based queries
- ✅ Audio streaming (browser-based)
- ✅ Gemini AI responses
- ✅ RAG knowledge retrieval
- ✅ Mock tool data

---

## OPTIONAL COMPONENT CHECKLIST

| Component | Need It? | Why/Why Not | Effort to Add |
|-----------|---------|-----------|--------------|
| MongoDB | No | Mock data works fine | 30 min |
| Redis | No | In-memory works | 1 hour |
| JWT Auth | No | Public API is OK for hackathon | 2 hours |
| Docker | No | Manual setup is simple | 1 hour |
| Monitoring | No | Logging is sufficient | 2-3 hours |
| Database Seeds | No | Use mock data or populate manually | 30 min |

---

## WHAT HAPPENS WITHOUT EACH OPTIONAL COMPONENT

### No MongoDB
```
✅ System starts and works
✅ All endpoints respond
✅ Tools return mock data:
   - get_customer_bill() → {"bill": 500, "due_date": "2026-08-30"}
   - get_payment_status() → {"status": "success"}
   - get_current_plan() → {"name": "Premium 5G"}
⚠️  No persistent customer information
⚠️  Customer data lost on backend restart
```

### No Redis
```
✅ System starts and works
✅ All endpoints respond
✅ Sessions stored in memory
⚠️  Session lost if backend restarts
⚠️  Can't scale to multiple backend instances
```

### No JWT Auth
```
✅ System starts and works
✅ All endpoints respond
⚠️  Anyone can call any endpoint
⚠️  No user identification
⚠️  No permission control
```

### No Docker
```
✅ System starts and works
✅ All endpoints respond
⚠️  Must have Python and Node.js installed manually
⚠️  More difficult to deploy to servers
⚠️  Potential OS-specific issues
```

### No Monitoring
```
✅ System starts and works
✅ All endpoints respond
✅ Logs appear in terminal
⚠️  No performance metrics
⚠️ No external logging
⚠️  Harder to debug production issues
```

---

## COMPARISON: WITH vs WITHOUT

### Text-Only Mode (No Audio)
```
WITHOUT Optional Components:
- Setup Time: 10 minutes
- Storage: ~500 MB
- Memory: 200-300 MB
- Features: ✅ Text queries, ✅ RAG, ✅ Mock tools, ✅ Gemini responses

WITH Optional Components:
- Setup Time: 1-2 hours
- Storage: 2-5 GB
- Memory: 500 MB - 1 GB
- Features: ✅ All above + ✅ Audio, ✅ Persistent data, ✅ Auth, ✅ Metrics
```

### Audio Mode (Gemini Live)
```
WITHOUT Optional Components:
- Setup Time: 15 minutes
- Storage: ~500 MB
- Memory: 200-300 MB
- Features: ✅ Audio streaming, ✅ Gemini Live, ✅ Mock tools

WITH Optional Components:
- Setup Time: 1-2 hours
- Storage: 2-5 GB
- Memory: 500 MB - 1 GB
- Features: ✅ All above + ✅ Persistent data, ✅ Auth, ✅ Caching
```

---

## TROUBLESHOOTING

### "ModuleNotFoundError: No module named 'google.genai'"
**Solution:** Install google-genai
```bash
pip install google-genai
```

### "GEMINI_API_KEY not found"
**Solution:** Add to .env
```bash
GEMINI_API_KEY=your_actual_key_here
```

### "MongoD connection refused"
**Solution:** MongoDB is optional! The system will use mock data.
Or start MongoDB:
```bash
docker run -d -p 27017:27017 mongo
```

### "WebSocket connection failed"
**Solution:** Ensure backend is running on port 8000
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### "Chrome blocks microphone access"
**Solution:** Use localhost (not IP address) or HTTPS
- ✅ http://localhost:5173 (works)
- ✅ https://yourdomain.com (works)
- ❌ http://192.168.x.x:5173 (blocked by Chrome)

---

## DEPLOYMENT RECOMMENDATIONS

### For Hackathon (Minimum Setup)
```
✅ Do: Skip Docker, MongoDB, Auth, Monitoring
✅ Do: Use in-memory sessions
✅ Do: Use mock tool data
✅ Time: ~15 minutes to setup
```

### For Staging (Medium Setup)
```
✅ Do: Add MongoDB for persistent data
✅ Do: Add Redis for caching
⚠️  Skip: JWT Auth (add later)
⚠️  Skip: Docker (manual fine for now)
✅ Time: ~1 hour to setup
```

### For Production (Full Setup)
```
✅ Do: All optional components
✅ Do: Add JWT authentication
✅ Do: Docker containerization
✅ Do: Monitoring and alerting
✅ Time: ~4-5 hours to setup
```

---

## FINAL RECOMMENDATION

**For Your Current Needs:**

**START WITH:**
1. Backend + Frontend (required only)
2. GEMINI_API_KEY
3. No MongoDB, Redis, or Docker

**THEN ADD (if you need it):**
1. MongoDB (for persistent customer data)
2. Docker (for deployment)
3. JWT Auth (for security)
4. Monitoring (for debugging)

**Total time to working system: ~20 minutes**

---

## SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────┐
│  FRONTEND (React/Vite)           REQUIRED       │
├─────────────────────────────────────────────────┤
│  - WebSocket Connection                         │
│  - Audio Recording (useAudioRecorder)           │
│  - Audio Playback (useAudioPlayer)              │
│  - Live Dashboard                               │
└──────────────┬──────────────────────────────────┘
               │ WebSocket
┌──────────────▼──────────────────────────────────┐
│  FastAPI Backend                 REQUIRED       │
├──────────────┬──────────────────────────────────┤
│  - WebSocket Handler             │              │
│  - Orchestrator                  │              │
│  - Supervisor Agent              │ Gemini Live  │
│  - Text Mode                     │ Audio (NEW)  │
│  - Audio Mode (NEW)              │              │
└──────────────┬──────────────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────┐           ┌───▼──────┐
│ Gemini │           │ RAG/     │
│ API    │ REQUIRED  │ Tools    │ REQUIRED
│        │           │ (Mock ok)│
└────────┘           └──────────┘
    ▲
    │
    └─── OPTIONAL ───┐
                     │
            ┌────────▼────────┐
            │ MongoDB         │
            │ Redis           │
            │ JWT Auth        │
            │ Monitoring      │
            │ Docker          │
            └─────────────────┘
```

---

## CONCLUSION

**You need:**
- Python, Node.js, Gemini API key, and the code (already have it)

**You don't need (will work without):**
- MongoDB, Redis, Docker, JWT Auth, Monitoring

**Start today with just the required components!**
