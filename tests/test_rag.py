import pytest

from backend.app.rag import RAGService


# ============================================================
# Sample NLU data
# ============================================================

VALID_NLU_DATA = {
    "request_id": "REQ001",

    "language": {
        "primary": "en",
        "code_switched": False,
    },

    "intent": {
        "name": "billing",
    },

    "entities": {
        "customer_id": "C001",
    },

    "sentiment": {
        "label": "negative",
    },

    "customer_query": (
        "Why is my bill higher this month?"
    ),
}


# ============================================================
# Fake QueryProcessor
# ============================================================

class FakeQueryProcessor:
    """
    Fake QueryProcessor used for unit testing RAGService.

    This prevents the test from requiring:
        - ChromaDB
        - Embedding model
        - Actual RAG documents
    """

    def __init__(
        self,
        top_k=3,
        score_threshold=0.50,
    ):
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.received_data = None

    def process(self, nlu_data):
        self.received_data = nlu_data

        return {
            "request_id": nlu_data["request_id"],

            "customer_context": {
                "language": nlu_data["language"]["primary"],
                "code_switched": nlu_data["language"]["code_switched"],
                "intent": nlu_data["intent"]["name"],
                "entities": nlu_data["entities"],
                "sentiment": nlu_data["sentiment"]["label"],
            },

            "customer_query": nlu_data["customer_query"],

            "retrieved_context": [
                {
                    "content": (
                        "Billing information for "
                        "monthly charges."
                    ),
                    "relevance_score": 0.91,
                    "source": "billing_guide",
                    "language": "en",
                }
            ],

            "response_requirements": {
                "language": nlu_data["language"]["primary"],
                "use_context_only": True,
                "do_not_invent_information": True,
            },
        }


# ============================================================
# Helper
# ============================================================

def create_test_service(monkeypatch):
    """
    Replace the real QueryProcessor with the fake one.
    """

    monkeypatch.setattr(
        "backend.app.rag.QueryProcessor",
        FakeQueryProcessor,
    )

    return RAGService(
        top_k=3,
        score_threshold=0.50,
    )


# ============================================================
# TEST 1
# ============================================================

def test_rag_service_initialization(monkeypatch):
    """
    Verify that RAGService initializes with
    the expected configuration.
    """

    service = create_test_service(
        monkeypatch
    )

    assert service.top_k == 3
    assert service.score_threshold == 0.50

    assert isinstance(
        service.processor,
        FakeQueryProcessor,
    )


# ============================================================
# TEST 2
# ============================================================

def test_retrieve_valid_nlu_data(monkeypatch):
    """
    Verify that valid NLU data is passed to
    QueryProcessor and RAG context is returned.
    """

    service = create_test_service(
        monkeypatch
    )

    result = service.retrieve(
        VALID_NLU_DATA
    )

    assert result is not None

    assert result["request_id"] == "REQ001"

    assert (
        result["customer_query"]
        == "Why is my bill higher this month?"
    )

    assert len(
        result["retrieved_context"]
    ) == 1


# ============================================================
# TEST 3
# ============================================================

def test_retrieve_passes_nlu_data_to_processor(
    monkeypatch,
):
    """
    Verify that RAGService does not modify
    the NLU data before passing it to
    QueryProcessor.
    """

    service = create_test_service(
        monkeypatch
    )

    service.retrieve(
        VALID_NLU_DATA
    )

    assert (
        service.processor.received_data
        == VALID_NLU_DATA
    )


# ============================================================
# TEST 4
# ============================================================

def test_retrieve_rejects_empty_data(monkeypatch):
    """
    Empty NLU data should raise ValueError.
    """

    service = create_test_service(
        monkeypatch
    )

    with pytest.raises(ValueError):
        service.retrieve({})


# ============================================================
# TEST 5
# ============================================================

def test_retrieve_rejects_non_dictionary(
    monkeypatch,
):
    """
    NLU data must be a dictionary.
    """

    service = create_test_service(
        monkeypatch
    )

    with pytest.raises(TypeError):
        service.retrieve(
            "invalid nlu data"
        )


# ============================================================
# TEST 6
# ============================================================

def test_retrieve_requires_request_id(
    monkeypatch,
):
    """
    request_id is required by the RAG pipeline.
    """

    service = create_test_service(
        monkeypatch
    )

    nlu_data = VALID_NLU_DATA.copy()

    nlu_data.pop(
        "request_id"
    )

    with pytest.raises(ValueError):
        service.retrieve(
            nlu_data
        )


# ============================================================
# TEST 7
# ============================================================

def test_retrieve_requires_intent(
    monkeypatch,
):
    """
    intent.name is required.
    """

    service = create_test_service(
        monkeypatch
    )

    nlu_data = VALID_NLU_DATA.copy()

    nlu_data["intent"] = {}

    with pytest.raises(ValueError):
        service.retrieve(
            nlu_data
        )


# ============================================================
# TEST 8
# ============================================================

def test_retrieve_requires_customer_query(
    monkeypatch,
):
    """
    customer_query is required.
    """

    service = create_test_service(
        monkeypatch
    )

    nlu_data = VALID_NLU_DATA.copy()

    nlu_data["customer_query"] = ""

    with pytest.raises(ValueError):
        service.retrieve(
            nlu_data
        )


# ============================================================
# TEST 9
# ============================================================

def test_search_creates_nlu_data(
    monkeypatch,
):
    """
    Verify the convenience search() method
    creates the expected NLU structure.
    """

    service = create_test_service(
        monkeypatch
    )

    result = service.search(
        query="Why is my bill high?",
        request_id="REQ002",
        language="en",
        intent="billing",
        entities={
            "customer_id": "C001"
        },
        sentiment="negative",
        code_switched=False,
    )

    received = (
        service.processor.received_data
    )

    assert received["request_id"] == "REQ002"

    assert (
        received["language"]["primary"]
        == "en"
    )

    assert (
        received["language"]["code_switched"]
        is False
    )

    assert (
        received["intent"]["name"]
        == "billing"
    )

    assert (
        received["entities"]["customer_id"]
        == "C001"
    )

    assert (
        received["sentiment"]["label"]
        == "negative"
    )

    assert (
        received["customer_query"]
        == "Why is my bill high?"
    )

    assert result["request_id"] == "REQ002"


# ============================================================
# TEST 10
# ============================================================

def test_search_rejects_empty_query(
    monkeypatch,
):
    """
    Empty query should raise ValueError.
    """

    service = create_test_service(
        monkeypatch
    )

    with pytest.raises(ValueError):
        service.search(
            query=""
        )


# ============================================================
# TEST 11
# ============================================================

def test_search_rejects_non_string_query(
    monkeypatch,
):
    """
    Query must be a string.
    """

    service = create_test_service(
        monkeypatch
    )

    with pytest.raises(TypeError):
        service.search(
            query=123
        )


# ============================================================
# TEST 12
# ============================================================

def test_retrieved_context_structure(
    monkeypatch,
):
    """
    Verify that the returned RAG context
    contains the fields expected by the
    agent/LLM layer.
    """

    service = create_test_service(
        monkeypatch
    )

    result = service.retrieve(
        VALID_NLU_DATA
    )

    assert "request_id" in result
    assert "customer_context" in result
    assert "customer_query" in result
    assert "retrieved_context" in result
    assert "response_requirements" in result

    context = result[
        "retrieved_context"
    ][0]

    assert "content" in context
    assert "relevance_score" in context
    assert "source" in context
    assert "language" in context


# ============================================================
# TEST 13
# ============================================================

def test_response_requirements(
    monkeypatch,
):
    """
    Verify that RAG context contains the
    expected safety requirements for the LLM.
    """

    service = create_test_service(
        monkeypatch
    )

    result = service.retrieve(
        VALID_NLU_DATA
    )

    requirements = result[
        "response_requirements"
    ]

    assert (
        requirements["use_context_only"]
        is True
    )

    assert (
        requirements[
            "do_not_invent_information"
        ]
        is True
    )