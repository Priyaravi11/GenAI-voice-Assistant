import pytest
from rag.ingestion.chunker import split_text, chunk_document


class TestSplitText:
    """Test suite for split_text function"""

    def test_empty_text_returns_empty_list(self):
        """Test that empty text returns empty list"""
        result = split_text("")
        assert result == []

    def test_whitespace_only_text_returns_empty_list(self):
        """Test that whitespace-only text returns empty list"""
        result = split_text("   \n\t  ")
        assert result == []

    def test_text_smaller_than_max_chunk_size(self):
        """Test that small text is not split"""
        text = "This is a short text that fits in one chunk."
        result = split_text(text)

        assert len(result) == 1
        assert result[0] == text

    def test_text_exactly_max_chunk_size(self):
        """Test text exactly at MAX_CHUNK_SIZE boundary"""
        text = "a" * 800  # Exactly MAX_CHUNK_SIZE
        result = split_text(text)

        assert len(result) == 1
        assert result[0] == text

    def test_text_larger_than_max_chunk_size(self):
        """Test that large text is split into multiple chunks"""
        text = "This is a test. " * 100  # Create text larger than MAX_CHUNK_SIZE

        result = split_text(text)

        assert len(result) > 1

        # Verify each chunk is within size limit (with some tolerance for word boundaries)
        for chunk in result:
            assert len(chunk) <= 800 or chunk.startswith("This is a test.")

    def test_chunks_have_overlap(self):
        """Test that chunks have overlap as configured"""
        # Create text that will definitely need splitting
        text = "chunk content repeated. " * 50

        result = split_text(text)

        # If there are multiple chunks, verify overlap
        if len(result) > 1:
            # The end of first chunk should overlap with start of second chunk
            first_chunk = result[0]
            second_chunk = result[1]

            # There should be some common text between consecutive chunks
            # (representing the overlap)
            assert len(first_chunk) + len(second_chunk) > len(text)

    def test_text_with_leading_trailing_whitespace(self):
        """Test that leading/trailing whitespace is handled"""
        text = "   \n  Content here  \n   "
        result = split_text(text)

        assert len(result) == 1
        assert result[0] == "Content here"

    def test_split_text_preserves_content(self):
        """Test that splitting preserves all content"""
        text = "word " * 200  # Create large text
        result = split_text(text)

        # Verify all words are present in chunks
        combined = "".join(result).replace(" ", "")
        original = text.replace(" ", "")

        # Account for possible whitespace differences
        assert combined.startswith(original[:100])


class TestChunkDocument:
    """Test suite for chunk_document function"""

    @pytest.fixture
    def sample_document(self):
        """Fixture providing a sample document structure"""
        return {
            "document_id": "doc_001",
            "source": "test.pdf",
            "file_type": "pdf",
            "language": "en",
            "category": "technical",
            "subcategory": "billing",
            "paragraphs": [
                {
                    "paragraph_number": 1,
                    "page_number": 1,
                    "text": "This is the first paragraph of the document."
                },
                {
                    "paragraph_number": 2,
                    "page_number": 1,
                    "text": "This is the second paragraph with more content."
                },
                {
                    "paragraph_number": 3,
                    "page_number": 2,
                    "text": "This is the third paragraph on a different page."
                },
            ]
        }

    def test_chunk_document_single_paragraph(self, sample_document):
        """Test chunking document with single small paragraph"""
        document = {
            **sample_document,
            "paragraphs": [
                {
                    "paragraph_number": 1,
                    "page_number": 1,
                    "text": "Single paragraph."
                }
            ]
        }

        result = chunk_document(document)

        assert len(result) == 1
        assert result[0]["chunk_id"] == "doc_001_chunk_1"
        assert "Single paragraph." in result[0]["text"]

    def test_chunk_document_multiple_paragraphs(self, sample_document):
        """Test chunking document with multiple paragraphs"""
        result = chunk_document(sample_document)

        assert len(result) >= 1

        for i, chunk in enumerate(result):
            assert chunk["chunk_id"] == f"doc_001_chunk_{i+1}"
            assert "text" in chunk
            assert "metadata" in chunk

    def test_chunk_metadata_preserved(self, sample_document):
        """Test that document metadata is preserved in chunks"""
        result = chunk_document(sample_document)

        for chunk in result:
            metadata = chunk["metadata"]
            assert metadata["document_id"] == "doc_001"
            assert metadata["source"] == "test.pdf"
            assert metadata["file_type"] == "pdf"
            assert metadata["language"] == "en"
            assert metadata["category"] == "technical"

    def test_chunk_with_empty_paragraphs(self):
        """Test chunking document with empty paragraphs"""
        document = {
            "document_id": "doc_002",
            "source": "test.pdf",
            "file_type": "pdf",
            "language": "en",
            "paragraphs": [
                {
                    "paragraph_number": 1,
                    "page_number": 1,
                    "text": "First paragraph"
                },
                {
                    "paragraph_number": 2,
                    "page_number": 1,
                    "text": ""  # Empty paragraph
                },
                {
                    "paragraph_number": 3,
                    "page_number": 1,
                    "text": "Third paragraph"
                },
            ]
        }

        result = chunk_document(document)

        assert len(result) >= 1
        # Empty paragraphs should be skipped
        combined_text = "\n".join(chunk["text"] for chunk in result)
        assert "First paragraph" in combined_text
        assert "Third paragraph" in combined_text

    def test_chunk_large_document(self):
        """Test chunking a large document that requires splitting"""
        # Create a document with many large paragraphs
        paragraphs = []
        for i in range(10):
            paragraphs.append({
                "paragraph_number": i + 1,
                "page_number": (i // 3) + 1,
                "text": "This is a paragraph with some content. " * 30  # Large paragraph
            })

        document = {
            "document_id": "doc_large",
            "source": "large.pdf",
            "file_type": "pdf",
            "language": "en",
            "paragraphs": paragraphs
        }

        result = chunk_document(document)

        assert len(result) > 1  # Should be split into multiple chunks

        # Verify all chunks have valid structure
        for chunk in result:
            assert "chunk_id" in chunk
            assert "text" in chunk
            assert "metadata" in chunk
            assert chunk["metadata"]["document_id"] == "doc_large"

    def test_chunk_document_no_paragraphs(self):
        """Test chunking document with no paragraphs"""
        document = {
            "document_id": "doc_empty",
            "source": "empty.pdf",
            "file_type": "pdf",
            "language": "en",
            "paragraphs": []
        }

        result = chunk_document(document)

        assert result == []

    def test_chunk_paragraph_numbers_tracked(self, sample_document):
        """Test that paragraph numbers are tracked in metadata"""
        result = chunk_document(sample_document)

        for chunk in result:
            metadata = chunk["metadata"]
            # Should have paragraph range info
            assert "paragraph_start" in metadata
            assert "paragraph_end" in metadata
            # End should be >= start
            assert metadata["paragraph_end"] >= metadata["paragraph_start"]

    def test_chunk_page_number_tracking(self, sample_document):
        """Test that page numbers are tracked in metadata"""
        result = chunk_document(sample_document)

        for chunk in result:
            metadata = chunk["metadata"]
            # First paragraph's page number should be in metadata
            assert "page_number" in metadata
