import pytest
from rag.embeddings.embedding_model import EmbeddingModel


class TestEmbeddingModel:
    """Test suite for EmbeddingModel class"""

    @pytest.fixture
    def embedding_model(self):
        """Fixture to initialize EmbeddingModel"""
        return EmbeddingModel()

    def test_embedding_model_initialization(self, embedding_model):
        """Test that embedding model initializes correctly"""
        assert embedding_model is not None
        assert embedding_model.model is not None
        assert embedding_model.dimension > 0

    def test_embed_single_text(self, embedding_model):
        """Test embedding a single text string"""
        text = "This is a test sentence for embedding."
        embedding = embedding_model.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) == embedding_model.dimension
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_text_with_unicode(self, embedding_model):
        """Test embedding text with Unicode characters"""
        text = "நிறுவனத்தின் சேவைகள் தமிழில் உபयோகம்"
        embedding = embedding_model.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) == embedding_model.dimension

    def test_embed_text_empty_string_raises_error(self, embedding_model):
        """Test that empty text raises ValueError"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            embedding_model.embed_text("")

    def test_embed_text_whitespace_only_raises_error(self, embedding_model):
        """Test that whitespace-only text raises ValueError"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            embedding_model.embed_text("   \n\t  ")

    def test_embed_documents_multiple(self, embedding_model):
        """Test embedding multiple documents"""
        texts = [
            "First document for testing.",
            "Second document for testing.",
            "Third document for testing.",
        ]
        embeddings = embedding_model.embed_documents(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == len(texts)

        for embedding in embeddings:
            assert isinstance(embedding, list)
            assert len(embedding) == embedding_model.dimension

    def test_embed_documents_empty_list(self, embedding_model):
        """Test embedding empty document list"""
        embeddings = embedding_model.embed_documents([])
        assert embeddings == []

    def test_embed_documents_unicode_multilingual(self, embedding_model):
        """Test embedding documents with multiple languages"""
        texts = [
            "English text for embedding.",
            "தமிழ் விவரணை",
            "हिंदी पाठ",
        ]
        embeddings = embedding_model.embed_documents(texts)

        assert len(embeddings) == len(texts)
        for embedding in embeddings:
            assert len(embedding) == embedding_model.dimension

    def test_embedding_dimension_consistency(self, embedding_model):
        """Test that get_dimension returns consistent value"""
        dim1 = embedding_model.get_dimension()
        dim2 = embedding_model.get_dimension()

        assert dim1 == dim2
        assert dim1 == embedding_model.dimension

    def test_different_texts_produce_different_embeddings(self, embedding_model):
        """Test that different texts produce different embeddings"""
        text1 = "How do I reset my password?"
        text2 = "Where is the nearest store?"

        embedding1 = embedding_model.embed_text(text1)
        embedding2 = embedding_model.embed_text(text2)

        # Embeddings should be different (at least some values should differ)
        assert embedding1 != embedding2

    def test_same_text_produces_same_embedding(self, embedding_model):
        """Test that same text produces identical embeddings"""
        text = "This is a consistent test."

        embedding1 = embedding_model.embed_text(text)
        embedding2 = embedding_model.embed_text(text)

        assert embedding1 == embedding2

    def test_embed_documents_long_text(self, embedding_model):
        """Test embedding long documents"""
        long_text = "This is a test document. " * 100  # Repeat to make it long
        texts = [long_text]

        embeddings = embedding_model.embed_documents(texts)

        assert len(embeddings) == 1
        assert len(embeddings[0]) == embedding_model.dimension

    def test_embedding_normalization(self, embedding_model):
        """Test that embeddings are normalized (approximately unit vectors)"""
        text = "Test text for normalization checking."
        embedding = embedding_model.embed_text(text)

        # Calculate L2 norm
        import math
        norm = math.sqrt(sum(x**2 for x in embedding))

        # For normalized embeddings, norm should be approximately 1.0
        assert abs(norm - 1.0) < 0.01  # Allow small tolerance
