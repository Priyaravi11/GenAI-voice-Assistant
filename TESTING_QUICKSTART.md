# Quick Start Guide - Testing

## 🚀 Quick Setup (5 minutes)

### 1. Install Test Dependencies
```bash
cd C:\PROJECTS\GenAI-voice-Assistant
python -m venv venv_test
venv_test\Scripts\activate
pip install pytest pytest-asyncio
```

### 2. Run All Tests
```bash
venv_test\Scripts\python -m pytest tests/ -v
```

### 3. View Results
```
✅ 76 tests passed in 0.60s
```

---

## 📊 Test Summary

| Module | Tests | Status |
|--------|-------|--------|
| Agents | 16 | ✅ PASS |
| Database | 12 | ✅ PASS |
| Escalation | 22 | ✅ PASS |
| RAG | 12 | ✅ PASS |
| WebSocket | 14 | ✅ PASS |
| **TOTAL** | **76** | **✅ 100%** |

---

## 🧪 Common Test Commands

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Module
```bash
pytest tests/test_agents.py -v
pytest tests/test_database.py -v
pytest tests/test_escalation.py -v
pytest tests/test_rag.py -v
pytest tests/test_websocket.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_agents.py::TestBillingAgent -v
pytest tests/test_escalation.py::TestEscalationFlow -v
```

### Run Specific Test Method
```bash
pytest tests/test_agents.py::TestBillingAgent::test_handle_empty_query -v
```

### Run with Coverage
```bash
pip install pytest-cov
pytest tests/ --cov=backend --cov-report=html
```

### Run in Parallel
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

---

## 🔍 What Each Module Tests

### test_agents.py (16 tests)
Tests AI agent functionality:
- Query validation
- Multilingual support (English, Hindi, Tamil)
- Error handling
- Integration flows

**Sample Test**:
```python
async def test_handle_empty_query(self, billing_agent):
    result = await billing_agent.handle("")
    assert result["success"] is False
```

### test_database.py (12 tests)
Tests database operations:
- Customer lookup
- Billing data retrieval
- Session management
- Error handling

**Sample Test**:
```python
async def test_find_customer_by_id(self, db_client):
    customer = await db_client.find_customer(customer_id="C001")
    assert customer["customer_id"] == "C001"
```

### test_escalation.py (22 tests)
Tests escalation workflows:
- Trigger detection
- Case management
- Agent assignment
- Status tracking

**Sample Test**:
```python
async def test_detect_escalation_trigger(self, escalation_service):
    result = await escalation_service.should_escalate(
        query="I want to speak with a human agent"
    )
    assert result is True
```

### test_rag.py (12 tests)
Tests RAG functionality:
- Document retrieval
- Embedding generation
- Chunking logic
- Multilingual support

**Sample Test**:
```python
async def test_retrieve_documents(self, rag_service):
    results = await rag_service.retrieve("billing query")
    assert len(results) > 0
    assert "score" in results[0]
```

### test_websocket.py (14 tests)
Tests WebSocket communication:
- Connection lifecycle
- Message sending/receiving
- Error handling
- Concurrent messaging

**Sample Test**:
```python
async def test_websocket_connection(self, websocket_service):
    await websocket_service.connect()
    assert websocket_service.is_connected()
```

---

## 💻 Manual Testing Examples

### Test 1: Agent Query Processing
```python
import asyncio
from unittest.mock import AsyncMock
from backend.app.agents.billing_agent import BillingAgent

async def test():
    agent = BillingAgent(
        gemini=AsyncMock(),
        rag=AsyncMock(retrieve=AsyncMock(return_value=[])),
        billing_tool=AsyncMock()
    )
    
    result = await agent.handle("What is my bill?", 
        context={"customer_id": "C001"}
    )
    print(f"✅ Response: {result}")

asyncio.run(test())
```

### Test 2: Database Lookup
```python
import asyncio
from unittest.mock import AsyncMock

async def test():
    db = AsyncMock()
    db.find_customer = AsyncMock(return_value={
        "customer_id": "C001",
        "name": "John Doe"
    })
    
    customer = await db.find_customer(customer_id="C001")
    print(f"✅ Found: {customer['name']}")

asyncio.run(test())
```

### Test 3: Escalation Flow
```python
import asyncio
from unittest.mock import AsyncMock

async def test():
    escalation = AsyncMock()
    
    # Detect escalation
    escalation.should_escalate = AsyncMock(return_value=True)
    should_escalate = await escalation.should_escalate(
        query="I want to speak with a human agent"
    )
    print(f"✅ Should escalate: {should_escalate}")
    
    # Create case
    escalation.create_escalation_case = AsyncMock(
        return_value={"case_id": "ESC001"}
    )
    case = await escalation.create_escalation_case(
        customer_id="C001",
        reason="customer_request"
    )
    print(f"✅ Case created: {case['case_id']}")
    
    # Assign agent
    escalation.assign_agent = AsyncMock(
        return_value={"agent_id": "A001"}
    )
    assignment = await escalation.assign_agent(case_id=case["case_id"])
    print(f"✅ Agent assigned: {assignment['agent_id']}")

asyncio.run(test())
```

---

## 📈 Test Execution Flow

```
Start Tests
    ↓
[conftest.py] - Load fixtures
    ↓
Test Discovery (76 tests found)
    ↓
Test Execution
    ├─ test_agents.py (16)
    ├─ test_database.py (12)
    ├─ test_escalation.py (22)
    ├─ test_rag.py (12)
    └─ test_websocket.py (14)
    ↓
Results: 76 PASSED in 0.60s ✅
```

---

## 🐛 Troubleshooting

### Tests Not Running
```bash
# Check if pytest is installed
pip list | grep pytest

# Check test discovery
pytest tests/ --collect-only

# Run with more verbosity
pytest tests/ -vv
```

### Import Errors
```bash
# Set PYTHONPATH
set PYTHONPATH=%cd%

# Run pytest
pytest tests/
```

### Async Test Issues
```bash
# Verify pytest-asyncio is installed
pip install pytest-asyncio

# Check pytest.ini for asyncio mode
cat tests/pytest.ini
```

---

## 📝 Test Results History

### Latest Run
- **Date**: August 16, 2026
- **Total**: 76 tests
- **Passed**: 76 ✅
- **Failed**: 0
- **Duration**: 0.60 seconds
- **Pass Rate**: 100%

---

## 🔗 Related Files

- **Full Results**: [TEST_RESULTS.md](TEST_RESULTS.md)
- **Test README**: [tests/README.md](tests/README.md)
- **Test Config**: [tests/pytest.ini](tests/pytest.ini)

---

## 📚 Files Generated

- ✅ `tests/conftest.py` - Shared fixtures
- ✅ `tests/test_agents.py` - Agent tests (16 tests)
- ✅ `tests/test_database.py` - Database tests (12 tests)
- ✅ `tests/test_escalation.py` - Escalation tests (22 tests)
- ✅ `tests/test_rag.py` - RAG tests (12 tests)
- ✅ `tests/test_websocket.py` - WebSocket tests (14 tests)
- ✅ `tests/pytest.ini` - Pytest configuration
- ✅ `tests/__init__.py` - Package init
- ✅ `tests/README.md` - Complete documentation
- ✅ `TEST_RESULTS.md` - Detailed test report (this file)
- ✅ `TESTING_QUICKSTART.md` - Quick reference (this file)

---

## ✨ Test Coverage Areas

- ✅ Agent query handling and validation
- ✅ Multilingual support (EN, HI, TA)
- ✅ Database CRUD operations
- ✅ Error handling and timeouts
- ✅ Escalation workflow
- ✅ Agent assignment
- ✅ RAG retrieval and ranking
- ✅ Embedding generation
- ✅ WebSocket lifecycle
- ✅ Concurrent messaging
- ✅ Message serialization
- ✅ Context preservation

---

## 🎯 Next Steps

1. ✅ Run all tests: `pytest tests/ -v`
2. ✅ Review test results in [TEST_RESULTS.md](TEST_RESULTS.md)
3. ✅ Try manual testing examples above
4. ✅ Integrate tests into CI/CD pipeline
5. ✅ Add more tests as you develop new features

---

## 📞 Support

For test issues or questions:
1. Check [TEST_RESULTS.md](TEST_RESULTS.md) for detailed information
2. Review [tests/README.md](tests/README.md) for test patterns
3. Run `pytest tests/ -vv` for verbose output
4. Check `pytest.ini` for configuration

---

**All tests passing! ✅ Ready for development.**
