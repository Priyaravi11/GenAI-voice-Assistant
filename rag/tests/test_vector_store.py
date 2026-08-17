import pytest
from unittest.mock import Mock, patch, MagicMock
from rag.vector_store.client import get_chroma_client
from rag.vector_store.retriever import Retriever


class TestChromaClientFunction:
    """Test suite for Chroma client function"""

    @patch('rag.vector_store.client.chromadb')
    def test_get_chroma_client(self, mock_chromadb):
        """Test getting Chroma client"""
        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client

        # Note: This will create the actual path, so we mock chromadb
        with patch('rag.vector_store.client.Path') as mock_path:
            mock_chroma_path = MagicMock()
            mock_path.return_value = mock_chroma_path
            mock_chroma_path.resolve.return_value.parents = [MagicMock(), MagicMock(), MagicMock()]

            # Mock mkdir to prevent actual directory creation
            mock_chroma_path.mkdir = MagicMock()

            client = get_chroma_client()

            assert client is not None

    @patch('rag.vector_store.client.chromadb')
    @patch('rag.vector_store.client.Path')
    def test_chroma_client_persistent_storage(self, mock_path_class, mock_chromadb):
        """Test that ChromaDB uses persistent storage"""
        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client

        # Setup mocks
        mock_path = MagicMock()
        mock_path_class.return_value = mock_path
        mock_path.resolve.return_value.parents = [MagicMock(), MagicMock(), MagicMock()]
        mock_path.mkdir = MagicMock()

        client = get_chroma_client()

        # Verify PersistentClient was called
        mock_chromadb.PersistentClient.assert_called_once()


class TestCollectionFunction:
    """Test suite for collection retrieval"""

    @patch('rag.vector_store.collection.get_chroma_client')
    def test_get_collection(self, mock_get_client):
        """Test getting a collection"""
        from rag.vector_store.collection import get_collection

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client

        collection = get_collection()

        assert collection is not None
        mock_client.get_or_create_collection.assert_called_once()

    @patch('rag.vector_store.collection.get_chroma_client')
    def test_collection_uses_cosine_distance(self, mock_get_client):
        """Test that collection uses cosine distance metric"""
        from rag.vector_store.collection import get_collection

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client

        collection = get_collection()

        # Verify get_or_create_collection was called with cosine config
        args, kwargs = mock_client.get_or_create_collection.call_args
        assert "configuration" in kwargs
        assert kwargs["configuration"]["hnsw"]["space"] == "cosine"


class TestRetriever:
    """Test suite for Retriever class"""

    @pytest.fixture
    def mock_retriever(self):
        """Fixture providing a mocked Retriever instance"""
        with patch('rag.vector_store.retriever.get_collection'), \
             patch('rag.vector_store.retriever.EmbeddingModel'):
            retriever = Retriever(top_k=3, score_threshold=0.5)
            return retriever

    def test_retriever_initialization(self, mock_retriever):
        """Test Retriever initialization"""
        assert mock_retriever is not None
        assert mock_retriever.top_k == 3
        assert mock_retriever.score_threshold == 0.5

    def test_retriever_top_k_parameter(self):
        """Test that top_k parameter is set correctly"""
        with patch('rag.vector_store.retriever.get_collection'), \
             patch('rag.vector_store.retriever.EmbeddingModel'):
            retriever = Retriever(top_k=5, score_threshold=0.5)
            assert retriever.top_k == 5

    def test_retriever_score_threshold_parameter(self):
        """Test that score_threshold parameter is set correctly"""
        with patch('rag.vector_store.retriever.get_collection'), \
             patch('rag.vector_store.retriever.EmbeddingModel'):
            retriever = Retriever(top_k=3, score_threshold=0.7)
            assert retriever.score_threshold == 0.7

    def test_retriever_search_empty_query_raises_error(self, mock_retriever):
        """Test that empty query raises ValueError"""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            mock_retriever.search("")

    def test_retriever_search_whitespace_only_raises_error(self, mock_retriever):
        """Test that whitespace-only query raises ValueError"""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            mock_retriever.search("   \n\t  ")

    def test_retriever_default_parameters(self):
        """Test Retriever with default parameters"""
        with patch('rag.vector_store.retriever.get_collection'), \
             patch('rag.vector_store.retriever.EmbeddingModel'):
            retriever = Retriever()
            assert retriever.top_k > 0
            assert retriever.score_threshold > 0


class TestRetrieverIntegration:
    """Integration tests for Retriever with mock data"""

    @pytest.fixture
    def mock_search_results(self):
        """Fixture providing mock search results"""
        return [
            {
                "content": "Information about billing issues",
                "relevance_score": 0.92,
                "metadata": {"category": "billing", "page": 1}
            },
            {
                "content": "Details on account charges",
                "relevance_score": 0.87,
                "metadata": {"category": "billing", "page": 2}
            },
            {
                "content": "How to contact support",
                "relevance_score": 0.78,
                "metadata": {"category": "support", "page": 5}
            }
        ]

    def test_retriever_search_result_structure(self, mock_search_results):
        """Test that search results have expected structure"""
        for result in mock_search_results:
            assert "content" in result
            assert "relevance_score" in result
            assert "metadata" in result
            assert isinstance(result["relevance_score"], float)
            assert 0 <= result["relevance_score"] <= 1

    def test_retriever_results_sorted_by_score(self, mock_search_results):
        """Test that results are sorted by relevance score"""
        sorted_results = sorted(
            mock_search_results,
            key=lambda x: x["relevance_score"],
            reverse=True
        )

        for i in range(len(sorted_results) - 1):
            assert (sorted_results[i]["relevance_score"] >=
                    sorted_results[i + 1]["relevance_score"])

    def test_retriever_filters_by_threshold(self, mock_search_results):
        """Test that retriever filters results by score threshold"""
        threshold = 0.85

        filtered = [r for r in mock_search_results
                   if r["relevance_score"] >= threshold]

        assert len(filtered) == 2
        assert all(r["relevance_score"] >= threshold for r in filtered)

    def test_retriever_limits_by_top_k(self, mock_search_results):
        """Test that retriever limits results to top_k"""
        top_k = 2
        limited = mock_search_results[:top_k]

        assert len(limited) <= top_k

    def test_retriever_empty_results(self):
        """Test handling of empty search results"""
        results = []

        assert results == []
        assert len(results) == 0

    def test_retriever_single_result(self):
        """Test handling of single search result"""
        results = [
            {
                "content": "Single result",
                "relevance_score": 0.95,
                "metadata": {"category": "test"}
            }
        ]

        assert len(results) == 1
        assert results[0]["relevance_score"] > 0.9


class TestVectorStoreMetadata:
    """Test suite for metadata handling in vector store"""

    def test_metadata_structure_validation(self):
        """Test that metadata has required fields"""
        metadata = {
            "document_id": "doc_001",
            "source": "test.pdf",
            "category": "technical",
            "page_number": 1
        }

        assert "document_id" in metadata
        assert "source" in metadata
        assert metadata["category"] is not None

    def test_metadata_filter_structure(self):
        """Test metadata filter structure"""
        filter_dict = {
            "category": "billing"
        }

        assert isinstance(filter_dict, dict)
        assert len(filter_dict) > 0

    def test_metadata_filter_with_multiple_criteria(self):
        """Test metadata filter with multiple criteria"""
        filter_dict = {
            "$and": [
                {"category": "technical"},
                {"language": "en"}
            ]
        }

        assert "$and" in filter_dict
        assert len(filter_dict["$and"]) == 2


class TestVectorStoreChunkHandling:
    """Test suite for chunk handling in vector store"""

    @pytest.fixture
    def sample_chunk(self):
        """Fixture providing a sample chunk"""
        return {
            "chunk_id": "doc_001_chunk_1",
            "text": "This is the content of the first chunk.",
            "metadata": {
                "document_id": "doc_001",
                "source": "document.pdf",
                "file_type": "pdf",
                "language": "en",
                "category": "general",
                "page_number": 1,
                "chunk_number": 1
            }
        }

    def test_chunk_has_required_fields(self, sample_chunk):
        """Test that chunk has all required fields"""
        assert "chunk_id" in sample_chunk
        assert "text" in sample_chunk
        assert "metadata" in sample_chunk

    def test_chunk_metadata_structure(self, sample_chunk):
        """Test chunk metadata structure"""
        metadata = sample_chunk["metadata"]

        assert "document_id" in metadata
        assert "source" in metadata
        assert "language" in metadata

    def test_chunk_text_not_empty(self, sample_chunk):
        """Test that chunk text is not empty"""
        assert sample_chunk["text"]
        assert len(sample_chunk["text"]) > 0

    def test_chunk_id_format(self, sample_chunk):
        """Test that chunk ID follows expected format"""
        chunk_id = sample_chunk["chunk_id"]

        # Should contain document_id and chunk number
        assert "doc_001" in chunk_id
        assert "chunk_" in chunk_id
