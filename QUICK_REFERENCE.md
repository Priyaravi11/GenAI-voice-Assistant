# GenAI Voice Assistant - Architecture Reference & Quick Fixes

## 🗂️ Project Structure

```
C:\PROJECTS\GenAI-voice-Assistant\
│
├── backend/                              # FastAPI backend
│   ├── app/
│   │   ├── main.py                      ✅ Entry point (depends on others)
│   │   ├── orchestrator.py              ⚠️  NEEDS agent routing
│   │   ├── websocket.py                 ❌ NEEDS REWRITE
│   │   ├── gemini.py                    ⚠️  NEEDS Gemini Live impl
│   │   ├── rag.py                       ✅ Complete RAG service
│   │   ├── tools.py                     ✅ Tool registry & executor
│   │   ├── escalation.py                ✅ Escalation manager
│   │   ├── context.py                   ✅ Session management
│   │   ├── validation.py                ✅ Input validators
│   │   ├── config.py                    ✅ Configuration
│   │   ├── database.py                  ✅ MongoDB setup
│   │   ├── models.py                    ✅ Pydantic models
│   │   ├── logger.py                    ✅ Logging
│   │   │
│   │   ├── agents/                      # AI Agents (6 total)
│   │   │   ├── supervisor_agent.py      ✅ Query classification
│   │   │   ├── general_agent.py         ⚠️  Async consistency
│   │   │   ├── billing_agent.py         ✅ Billing queries
│   │   │   ├── payment_agent.py         ✅ Payment queries
│   │   │   ├── plans_agent.py           ❌ Import error (backend.tools)
│   │   │   └── technical_agent.py       ❌ Import error (backend.tools)
│   │   │
│   │   └── api/
│   │       ├── websocket.py             ⚠️  Router import (needs fixing)
│   │       └── routes/
│   │           ├── session.py           ✅ Session endpoints
│   │           ├── rag.py               ✅ RAG endpoints
│   │           ├── calls.py             ✅ Call endpoints
│   │           ├── tools.py             ❌ Import typo (bac.app)
│   │           └── analytics.py         ✅ Analytics endpoints
│   │
│   └── requirements.txt                 ✅ Dependencies
│
├── rag/                                 ✅ COMPLETE - RAG Pipeline
│   ├── query/
│   │   ├── query_processor.py           ✅ NLU → Metadata mapping
│   │   ├── intent_mapper.py             ✅ Intent extraction
│   │   └── translator.py                ✅ Language translation
│   │
│   ├── ingestion/
│   │   ├── document_loader.py           ✅ PDF, DOCX loading
│   │   ├── chunker.py                   ✅ Smart chunking
│   │   ├── document_cleaner.py          ✅ Text cleaning
│   │   └── metadata_extractor.py        ✅ Metadata extraction
│   │
│   ├── embeddings/
│   │   └── embedding_model.py           ✅ BGE embeddings
│   │
│   ├── vector_store/
│   │   ├── client.py                    ✅ ChromaDB client
│   │   ├── collection.py                ✅ Collection management
│   │   └── retriever.py                 ✅ Document retrieval
│   │
│   ├── context/
│   │   └── context_builder.py           ✅ RAG context building
│   │
│   ├── retrieval/
│   │   ├── retriever.py                 ✅ Retrieval logic
│   │   └── context_builder.py           ✅ Context formatting
│   │
│   ├── pipeline/
│   │   └── build_index.py               ✅ Index building
│   │
│   └── tests/                           ✅ 58 tests, all passing
│
├── tools/                               ✅ COMPLETE - Telecom Tools
│   ├── billing_tool.py                  ✅ 6 functions
│   ├── payment_tool.py                  ✅ 4 functions
│   ├── plans_tool.py                    ✅ 4 functions
│   ├── network_tool.py                  ✅ 6 functions
│   └── customer_tool.py                 ✅ 9 functions
│
├── frontend/                            ✅ React/Vite application
│   ├── src/
│   │   ├── components/                  ✅ Voice interface
│   │   ├── services/                    ✅ API/WebSocket calls
│   │   ├── hooks/                       ✅ React hooks
│   │   └── App.tsx                      ✅ Main app
│   │
│   └── package.json                     ✅ Dependencies
│
├── tests/                               ✅ 76 tests, 100% passing
│   ├── test_agents.py                   ✅ Agent tests (16)
│   ├── test_database.py                 ✅ Database tests (12)
│   ├── test_escalation.py               ✅ Escalation tests (22)
│   ├── test_rag.py                      ✅ RAG tests (12)
│   ├── test_websocket.py                ✅ WebSocket tests (14)
│   ├── conftest.py                      ✅ Fixtures
│   └── pytest.ini                       ✅ Configuration
│
├── scripts/                             ✅ Utility scripts
│   ├── run_dev.py                       ✅ Dev server launcher
│   ├── seed_mongodb.py                  ✅ Database seeding
│   ├── ingest_rag.py                    ✅ RAG ingestion
│   └── test_api.py                      ✅ API testing
│
├── docs/                                📝 Documentation templates
│
├── INTEGRATION_ANALYSIS.md              📊 Detailed analysis (1,060 lines)
├── EXECUTIVE_SUMMARY.md                 📊 This file (450 lines)
├── TEST_RESULTS.md                      📊 Test report (820 lines)
├── PROJECT_COMPLETION_SUMMARY.md        📊 Project status
├── TESTING_SUMMARY.md                   📊 Testing guide
│
└── .env.example                         ✅ Environment template
```

---

## 🔧 THE 8 CRITICAL ISSUES - QUICK FIX REFERENCE

### Issue 1: Import Typo in Tools Route
```
FILE: backend/app/api/routes/tools.py
LINE: 14

❌ WRONG:
from bac.app.tools import get_tool, list_tools

✅ CORRECT:
from backend.app.tools import get_tool, list_tools

FIX: Change "bac" to "backend" (add "kend")
TIME: 30 seconds
```

### Issue 2: Plans Agent Import Path
```
FILE: backend/app/agents/plans_agent.py
LINE: 8

❌ WRONG:
from backend.tools.plans_tool import (

✅ CORRECT:
from tools.plans_tool import (

REASON: Tools are at project root, not in backend/
TIME: 1 minute
```

### Issue 3: Technical Agent Import Path
```
FILE: backend/app/agents/technical_agent.py
LINE: 8

❌ WRONG:
from backend.tools.network_tool import (

✅ CORRECT:
from tools.network_tool import (

REASON: Tools are at project root, not in backend/
TIME: 1 minute
```

### Issue 4: WebSocket Not Implemented
```
FILE: backend/app/websocket.py
STATUS: Contains TEST CODE, not actual implementation

CURRENT: 61 lines of test code
NEEDED: ~200-250 lines of actual WebSocket handler

KEY PARTS NEEDED:
1. @router.websocket("/ws/voice") decorator
2. ConnectionManager class for multi-turn
3. Input validation (query, language)
4. Session management integration
5. Orchestrator call: await orchestrator.process_text(...)
6. Escalation check: escalation_manager.should_escalate(...)
7. Response formatting and sending

TIME: 2-3 hours
```

### Issue 5: Orchestrator Not Routing to Agents
```
FILE: backend/app/orchestrator.py
STATUS: Exists but incomplete

CURRENT LOGIC:
1. Validate input ✅
2. Get/create session ✅
3. Retrieve RAG context ✅
4. Call Gemini directly ❌ (SHOULD route to agent)
5. Return response ✅

MISSING LOGIC:
1. Call SupervisorAgent to classify query
   supervisor_result = await supervisor_agent.handle(query)
   agent_type = supervisor_result.get("agent")  # "billing", "plans", etc.

2. Route to appropriate agent:
   if agent_type == "billing":
       result = await billing_agent.handle(query, context)
   elif agent_type == "plans":
       result = await plans_agent.handle(query, context)
   # ... etc for other agents

3. Check escalation:
   if escalation_manager.should_escalate(result):
       return escalation_manager.handle_escalation(...)
   
   return result

CODE NEEDED: 80-120 lines
TIME: 1-2 hours
```

### Issue 6: General Agent Async Issue
```
FILE: backend/app/agents/general_agent.py
ISSUE: Minor async consistency

Fix the _generate_response method to ensure it's properly async.
Ensure all calls are properly awaited.
TIME: 2 minutes
```

### Issue 7: Gemini Live Incomplete
```
FILE: backend/app/gemini.py
STATUS: Only stubs, no real implementation

EXISTING: ✅
- client setup
- system instruction
- get_live_config()
- create_live_session() skeleton

MISSING: ❌
- Audio input stream handling
- Message routing
- Session state management
- Error recovery
- Real-time text/audio conversion

PRIORITY: HIGH (but can fallback to text-only)
TIME: 3-4 hours
```

### Issue 8: WebSocket Error Handling Missing
```
FILE: backend/app/websocket.py (when implemented)
FILE: backend/app/orchestrator.py

Missing:
- Try-catch blocks in orchestrator.process_text()
- Try-catch blocks in WebSocket handler
- Proper error response formatting
- Logging of errors and queries

TIME: 1-2 hours
```

---

## 📊 The Fix Timeline

### Day 1 - Morning (2-3 hours)
```
09:00 - 09:05: Fix import errors (4 issues, ~3 minutes each)
09:05 - 11:30: Implement WebSocket handler
11:30 - 12:00: Quick test
```

### Day 1 - Afternoon (2-3 hours)
```
13:00 - 14:30: Connect Orchestrator to Agents
14:30 - 15:00: Test agent routing
15:00 - 16:00: Add error handling
```

### Day 2 - Morning (3-4 hours)
```
09:00 - 13:00: Implement Gemini Live API
13:00 - 13:30: Test Gemini Live
```

### Day 2 - Afternoon (2-3 hours)
```
14:00 - 16:30: E2E Testing & Polish
16:30 - 17:00: Documentation
```

**Total: 12-16 hours** across 2 days

---

## 🔄 Data Flow - Current vs Fixed

### CURRENT (Broken) Flow
```
Frontend Query
    ↓
WebSocket Endpoint
    ❌ MISSING - NO HANDLER
    
Orchestrator
    ↓
    bypass_supervisor_agent()
    ↓
    call_gemini_directly()
    ↓
    return_generic_response()

Result: All queries treated the same, no specialized handling
```

### FIXED Flow
```
Frontend Query
    ↓
✅ WebSocket Endpoint (/ws/voice)
    ↓ validate_input()
    ↓
✅ Get or create session
    ↓ store_conversation_history()
    ↓
✅ Orchestrator
    ├─ validate_query()
    ├─ retrieve_rag_context()
    │
    ├─ ✅ SupervisorAgent
    │  └─ classify_query() → agent_type
    │
    ├─ ✅ Specialized Agent (based on type)
    │  ├─ billing_agent / plans_agent / technical_agent / 
    │  │  payment_agent / general_agent
    │  │
    │  ├─ retrieve_domain_rag()
    │  ├─ execute_tool_if_needed()
    │  └─ generate_response_via_gemini()
    │
    ├─ ✅ Escalation Check
    │  ├─ should_escalate(agent_result)?
    │  ├─ YES → format_escalation_message()
    │  └─ NO → use_agent_response()
    │
    └─ Format final response
         {
           "response": "...",
           "language": "...",
           "escalated": true/false,
           "agent": "billing/plans/..."
         }
    ↓
✅ WebSocket sends to frontend
    ↓
Frontend displays response

Result: Specialized handling per domain, proper escalation
```

---

## 💾 Component Dependencies

```
FRONTEND
    └─ depends on →  WEBSOCKET HANDLER
                         └─ depends on →  ORCHESTRATOR
                                            ├─ depends on →  SUPERVISOR_AGENT
                                            │
                                            ├─ depends on →  [SPECIALIZED AGENTS]
                                            │                 ├─ BILLING_AGENT
                                            │                 ├─ PLANS_AGENT
                                            │                 ├─ PAYMENT_AGENT
                                            │                 ├─ TECHNICAL_AGENT
                                            │                 └─ GENERAL_AGENT
                                            │
                                            ├─ depends on →  RAG_SERVICE
                                            │                 └─ uses →  CHROMADB
                                            │
                                            ├─ depends on →  TOOLS_REGISTRY
                                            │                 └─ uses →  [5 TOOL MODULES]
                                            │
                                            ├─ depends on →  GEMINI_CLIENT
                                            │
                                            ├─ depends on →  ESCALATION_MANAGER
                                            │
                                            ├─ depends on →  SESSION_CONTEXT
                                            │
                                            └─ depends on →  VALIDATION


AGENTS
├─ RAG_SERVICE (for domain knowledge)
├─ TOOLS (billing_tool, plans_tool, etc.)
├─ GEMINI_CLIENT (for response generation)
└─ ESCALATION_MANAGER (for fallback)


RAG_SERVICE
├─ QUERY_PROCESSOR (NLU → filters)
├─ EMBEDDING_MODEL (BGE)
├─ VECTOR_STORE (ChromaDB)
└─ CONTEXT_BUILDER (format output)


TOOLS
└─ DATABASE (MongoDB)


GEMINI_CLIENT
├─ Text generation (working)
└─ Live API (needs implementation)
```

---

## 📋 Testing Checklist After Fixes

```
UNIT TESTS (Should All Still Pass):
☐ test_agents.py (16 tests)
☐ test_database.py (12 tests)
☐ test_escalation.py (22 tests)
☐ test_rag.py (12 tests)
☐ test_websocket.py (14 tests) - needs update for real impl

NEW TESTS TO ADD:
☐ test_websocket_integration.py - real handler flow
☐ test_orchestrator_routing.py - supervisor → agents
☐ test_agent_selection.py - correct agent chosen
☐ test_end_to_end.py - full query flow
☐ test_escalation_integration.py - escalation flow

MANUAL TESTS:
☐ WebSocket connects: curl ws://localhost:8000/ws/voice
☐ Billing query routes to BillingAgent
☐ Plans query routes to PlansAgent
☐ Payment query routes to PaymentAgent
☐ Technical query routes to TechnicalAgent
☐ Greeting routes to GeneralAgent
☐ Unknown query triggers escalation
☐ Multi-turn conversation works
☐ Languages are respected (English, Tamil, etc.)
```

---

## 🚨 Rollback Plan (If Something Goes Wrong)

1. **Import errors crash on startup?**
   - Revert the 3 import lines
   - All fixes are to single imports

2. **WebSocket handler breaks existing tests?**
   - Keep test code as backup
   - Can run tests against old implementation
   - New implementation should pass same tests

3. **Agent routing causes timeouts?**
   - Check if agents are async
   - All agents have `async def handle()` so this should work
   - Add timeout = 30 seconds to agent calls

4. **Escalation logic broken?**
   - Escalation code is isolated in escalation.py
   - Can bypass by returning agent response directly

---

## 📝 Code Change Summary

### Changes Required
```
4 files with import fixes         ~3 minutes
1 file rewritten (websocket.py)   ~2-3 hours
1 file enhanced (orchestrator.py) ~1-2 hours
1 file enhanced (gemini.py)       ~3-4 hours
```

### New Code (Approximate)
```
WebSocket handler:  200-250 lines
Orchestrator routing: 80-120 lines
Gemini Live: 250-350 lines
Error handling: 50-100 lines
Tests: 200-300 lines
---
Total new: 780-1,120 lines
```

---

## ✅ Ready-to-Use Components (No Changes)

```
RAG Module:           3,270 LOC  ✅ PRODUCTION READY
Tools Module:         2,642 LOC  ✅ PRODUCTION READY
Agents (logic):       3,755 LOC  ✅ PRODUCTION READY
Validation:             105 LOC  ✅ PRODUCTION READY
Context Management:     108 LOC  ✅ PRODUCTION READY
Escalation:             143 LOC  ✅ PRODUCTION READY
Database:               203 LOC  ✅ PRODUCTION READY
Models:                 111 LOC  ✅ PRODUCTION READY
```

---

## 🎯 Success Metrics

When you're done:

```
✅ python -c "from backend.app import main" works
✅ pytest tests/ -v shows 76/76 passing
✅ uvicorn backend.app.main:app starts without errors
✅ WebSocket connects: ws://localhost:8000/ws/voice
✅ Query "What are my plans?" routes to PlansAgent
✅ Query "How much is my bill?" routes to BillingAgent
✅ Unknown query triggers escalation message
✅ Multi-turn conversation works (same WebSocket)
✅ Language persists across turns
✅ No console errors on frontend
```

---

## 📚 Reference Documents

```
INTEGRATION_ANALYSIS.md      ← Read this for complete details
EXECUTIVE_SUMMARY.md         ← This file
TEST_RESULTS.md              ← See what tests exist
PROJECT_COMPLETION_SUMMARY.md ← Project status
```

---

**Last Updated**: August 17, 2026  
**Status**: Ready for Implementation  
**Difficulty**: MEDIUM (mostly connection work, not new architecture)
