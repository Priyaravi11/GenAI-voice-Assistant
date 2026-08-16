# GenAI Voice Assistant - Test Suite

Comprehensive test suite for the GenAI Voice Assistant backend. Tests cover agents, database operations, RAG functionality, WebSocket communication, and escalation flows.

## Project Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini               # Pytest configuration
├── test_agents.py          # Tests for AI agents (billing, technical, etc.)
├── test_database.py        # Tests for database operations
├── test_rag.py            # Tests for RAG retrieval and embeddings
├── test_websocket.py       # Tests for WebSocket communication
├── test_escalation.py      # Tests for human agent escalation
├── test_tools.py           # Tests for tool integration (empty)
├── test_orchestrator.py    # Tests for orchestration (empty)
├── test_gemini.py          # Tests for Gemini integration (empty)
└── __init__.py             # Package initialization
```

## Test Files

### conftest.py
Shared pytest fixtures and configuration:
- `mock_gemini`: Mock Gemini API client
- `mock_rag`: Mock RAG service
- `mock_database`: Mock database client
- `mock_billing_tool`: Mock billing tool
- `sample_context`: Sample context data
- `sample_query`: Sample query for testing

### test_agents.py
Tests for AI agents:
- `TestBillingAgent`: Billing agent functionality
  - Query validation
  - RAG retrieval
  - Customer data fetching
  - Response generation
- `TestBillingAgentIntegration`: Integration scenarios

### test_database.py
Tests for database operations:
- `TestDatabaseOperations`: Core database operations
  - Customer lookup
  - Billing data retrieval
  - Session management
  - Call logging
- `TestDatabaseIntegration`: Complete flow integration

### test_rag.py
Tests for RAG (Retrieval-Augmented Generation):
- `TestRAGRetrieval`: Document retrieval
  - Basic retrieval
  - Similarity scoring
  - Multilingual queries
- `TestEmbedding`: Embedding generation
- `TestDocumentChunking`: Document chunking logic
- `TestRAGIntegration`: Complete RAG pipeline

### test_websocket.py
Tests for WebSocket communication:
- `TestWebSocketConnection`: Connection lifecycle
  - Connect/disconnect
  - Authentication
  - Failures and timeouts
- `TestWebSocketMessaging`: Message handling
  - Send/receive messages
  - Message serialization
  - Error messages
- `TestWebSocketLifecycle`: Session lifecycle
  - Complete session flow
  - Multiple queries
  - Reconnection
- `TestWebSocketIntegration`: Concurrent messaging

### test_escalation.py
Tests for escalation and human agent features:
- `TestEscalationDetection`: Trigger detection
  - Explicit requests
  - Repeated failures
  - Sentiment analysis
- `TestEscalationCaseManagement`: Case lifecycle
  - Case creation
  - Status tracking
  - Priority levels
- `TestAgentAssignment`: Agent assignment
  - Least busy agent selection
  - Queue management
- `TestEscalationStatus`: Status transitions
- `TestEscalationIntegration`: Complete escalation flow

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test file
```bash
pytest tests/test_agents.py
```

### Run specific test class
```bash
pytest tests/test_agents.py::TestBillingAgent
```

### Run specific test
```bash
pytest tests/test_agents.py::TestBillingAgent::test_handle_empty_query
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run only async tests
```bash
pytest tests/ -m asyncio
```

### Run with coverage
```bash
pytest tests/ --cov=backend --cov-report=html
```

### Run tests in parallel (requires pytest-xdist)
```bash
pytest tests/ -n auto
```

## Configuration

The `pytest.ini` file contains:
- Test discovery patterns
- Pytest markers for organizing tests
- Asyncio mode configuration
- Output formatting
- Test timeout settings (300 seconds)

## Fixtures

All fixtures are defined in `conftest.py`:

### Mock Services
- `mock_gemini`: Async mock for Gemini API
- `mock_rag`: Async mock for RAG service
- `mock_database`: Async mock for database
- `mock_billing_tool`: Async mock for billing tool

### Test Data
- `sample_context`: Default context with customer_id, session_id, language
- `sample_query`: Default test query

### Event Loop
- `event_loop`: Creates new event loop for each async test

## Test Patterns

All test classes follow consistent patterns:

```python
@pytest.mark.asyncio
class TestFeature:
    """Test cases for a feature."""
    
    @pytest.fixture
    def service(self, mock_dependency):
        """Create service with mock dependencies."""
        return Service(mock_dependency)
    
    async def test_scenario(self, service):
        """Test a specific scenario."""
        result = await service.method()
        assert result is not None
```

## Adding New Tests

1. Create test file: `test_feature.py`
2. Import conftest fixtures
3. Create test classes with `Test` prefix
4. Create test methods with `test_` prefix
5. Use `@pytest.mark.asyncio` for async tests
6. Use fixtures from conftest for mocked dependencies

Example:
```python
import pytest
from backend.app.module import Service

@pytest.mark.asyncio
class TestService:
    
    @pytest.fixture
    def service(self, mock_dependency):
        return Service(mock_dependency)
    
    async def test_operation(self, service):
        result = await service.operation()
        assert result == expected
```

## Mocking Guidelines

- Use `AsyncMock` for async functions
- Use `MagicMock` for sync functions
- Set return values with `return_value` parameter
- Set side effects with `side_effect` parameter
- Check calls with `.assert_called_with()`, `.assert_called_once()`, etc.

Example:
```python
mock_service.method = AsyncMock(return_value="result")
mock_service.method.side_effect = Exception("error")
mock_service.method.assert_called_with(arg1, arg2)
```

## CI/CD Integration

Run tests in CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Run tests
  run: pytest tests/ --cov=backend --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

## Dependencies

Test suite requires:
- `pytest` (from requirements.txt)
- `pytest-asyncio` (from requirements.txt)
- `pytest-cov` (optional, for coverage reports)
- `pytest-xdist` (optional, for parallel execution)

Install test dependencies:
```bash
pip install -r requirements.txt
pip install pytest-cov pytest-xdist
```

## Notes

- All test files are initially empty placeholders
- Tests are designed to work with mocked dependencies
- Fixtures follow AAA pattern: Arrange, Act, Assert
- Tests are isolated and can run in any order
- Async tests use pytest-asyncio
- Configuration in pytest.ini enables auto-async mode

## Future Enhancements

- Add performance tests
- Add load tests for WebSocket
- Add E2E tests with real services
- Add contract tests for API
- Add property-based tests with hypothesis
- Add snapshot testing for responses
