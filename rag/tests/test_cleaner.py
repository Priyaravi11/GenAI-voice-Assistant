import pytest
from rag.ingestion.document_cleaner import (
    clean_text,
    clean_pdf_document,
    clean_docx_document,
    clean_document,
)


class TestCleanText:
    """Test suite for clean_text function"""

    def test_clean_empty_text(self):
        """Test cleaning empty text"""
        result = clean_text("")
        assert result == ""

    def test_clean_whitespace_only(self):
        """Test cleaning whitespace-only text"""
        result = clean_text("   \n\t  ")
        assert result == ""

    def test_normalize_windows_line_endings(self):
        """Test normalization of Windows line endings"""
        text = "First line\r\nSecond line\r\nThird line"
        result = clean_text(text)
        assert "\r\n" not in result
        assert "First line" in result
        assert "Second line" in result

    def test_normalize_old_mac_line_endings(self):
        """Test normalization of old Mac line endings"""
        text = "First line\rSecond line\rThird line"
        result = clean_text(text)
        assert "\r" not in result

    def test_replace_tabs_with_spaces(self):
        """Test that tabs are replaced with spaces"""
        text = "Column1\tColumn2\tColumn3"
        result = clean_text(text)
        assert "\t" not in result
        assert "Column1" in result
        assert "Column2" in result

    def test_remove_leading_trailing_line_whitespace(self):
        """Test removal of leading/trailing whitespace from lines"""
        text = "   Line with leading spaces\n\tLine with tabs\t  "
        result = clean_text(text)
        assert result.startswith("Line with leading")
        assert "Line with leading spaces" in result

    def test_remove_empty_lines(self):
        """Test that empty lines are removed"""
        text = "First line\n\n\nSecond line\n\nThird line"
        result = clean_text(text)
        # Should not have consecutive empty lines
        assert "\n\n\n" not in result

    def test_collapse_multiple_spaces(self):
        """Test that multiple consecutive spaces are collapsed"""
        text = "Word1   Word2    Word3     Word4"
        result = clean_text(text)
        assert "   " not in result
        assert "Word1 Word2" in result

    def test_normalize_excessive_blank_lines(self):
        """Test that excessive blank lines are normalized"""
        text = "Line 1\n\n\n\n\nLine 2"
        result = clean_text(text)
        # Should have at most 2 consecutive newlines (one blank line)
        assert "\n\n\n" not in result

    def test_preserve_unicode_characters(self):
        """Test that Unicode characters are preserved"""
        text = "தமிழ் விவரணை\nहिंदी टिप्पणी\nTelugu వర్ణన"
        result = clean_text(text)
        assert "தமிழ்" in result
        assert "हिंदी" in result
        assert "వర్ణన" in result

    def test_strip_final_result(self):
        """Test that final result is stripped of leading/trailing whitespace"""
        text = "\n\n  Content here  \n\n"
        result = clean_text(text)
        assert result == "Content here"

    def test_clean_real_document_excerpt(self):
        """Test cleaning a realistic document excerpt"""
        text = """
        
        This  is   a   poorly   formatted   document.
        
        
        It has   multiple   spacing   issues.
        
        And various    line    ending    problems.
        
        
        """
        result = clean_text(text)
        assert "This is a poorly formatted document." in result
        assert "\n\n\n" not in result


class TestCleanPdfDocument:
    """Test suite for clean_pdf_document function"""

    @pytest.fixture
    def sample_pdf_document(self):
        """Fixture providing a sample PDF document"""
        return {
            "document_id": "pdf_001",
            "source": "test.pdf",
            "file_type": "pdf",
            "language": "en",
            "total_pages": 2,
            "pages": [
                {
                    "page_number": 1,
                    "text": "   First  page   content  \n\nwith   issues   \n\n\n"
                },
                {
                    "page_number": 2,
                    "text": "\r\nSecond page with old line endings\r\n\r\n"
                },
            ]
        }

    def test_clean_pdf_document_basic(self, sample_pdf_document):
        """Test basic PDF document cleaning"""
        result = clean_pdf_document(sample_pdf_document)

        assert result["document_id"] == "pdf_001"
        assert len(result["pages"]) == 2

    def test_clean_pdf_preserves_page_numbers(self, sample_pdf_document):
        """Test that page numbers are preserved"""
        result = clean_pdf_document(sample_pdf_document)

        assert result["pages"][0]["page_number"] == 1
        assert result["pages"][1]["page_number"] == 2

    def test_clean_pdf_cleans_text_content(self, sample_pdf_document):
        """Test that page text is cleaned"""
        result = clean_pdf_document(sample_pdf_document)

        # Text should be cleaned
        first_page_text = result["pages"][0]["text"]
        assert "First page content" in first_page_text
        assert "\n\n\n" not in first_page_text

    def test_clean_pdf_removes_empty_pages(self):
        """Test that empty pages are removed"""
        document = {
            "document_id": "pdf_002",
            "source": "test.pdf",
            "file_type": "pdf",
            "language": "en",
            "pages": [
                {
                    "page_number": 1,
                    "text": "Content on page 1"
                },
                {
                    "page_number": 2,
                    "text": "   \n\n   "  # Empty page
                },
            ]
        }

        result = clean_pdf_document(document)

        # Empty pages should be removed
        assert len(result["pages"]) == 1

    def test_clean_pdf_document_structure(self, sample_pdf_document):
        """Test that document structure is maintained"""
        result = clean_pdf_document(sample_pdf_document)

        # All original fields should be present
        assert "document_id" in result
        assert "source" in result
        assert "file_type" in result
        assert "language" in result


class TestCleanDocxDocument:
    """Test suite for clean_docx_document function"""

    @pytest.fixture
    def sample_docx_document(self):
        """Fixture providing a sample DOCX document"""
        return {
            "document_id": "docx_001",
            "source": "test.docx",
            "file_type": "docx",
            "language": "en",
            "total_pages": None,
            "paragraphs": [
                {
                    "paragraph_number": 1,
                    "text": "   First   paragraph   with   spacing   \n"
                },
                {
                    "paragraph_number": 2,
                    "text": "Second\tparagraph\twith\ttabs"
                },
            ]
        }

    def test_clean_docx_document_basic(self, sample_docx_document):
        """Test basic DOCX document cleaning"""
        result = clean_docx_document(sample_docx_document)

        assert result["document_id"] == "docx_001"
        assert len(result["paragraphs"]) == 2

    def test_clean_docx_preserves_paragraph_numbers(self, sample_docx_document):
        """Test that paragraph numbers are preserved"""
        result = clean_docx_document(sample_docx_document)

        assert result["paragraphs"][0]["paragraph_number"] == 1
        assert result["paragraphs"][1]["paragraph_number"] == 2

    def test_clean_docx_cleans_paragraph_text(self, sample_docx_document):
        """Test that paragraph text is cleaned"""
        result = clean_docx_document(sample_docx_document)

        first_para = result["paragraphs"][0]["text"]
        assert "First paragraph with spacing" in first_para
        # Multiple spaces should be collapsed
        assert "   " not in first_para

    def test_clean_docx_removes_empty_paragraphs(self):
        """Test that empty paragraphs are removed"""
        document = {
            "document_id": "docx_002",
            "source": "test.docx",
            "file_type": "docx",
            "language": "en",
            "paragraphs": [
                {
                    "paragraph_number": 1,
                    "text": "Content in paragraph 1"
                },
                {
                    "paragraph_number": 2,
                    "text": "   \n\t  "  # Empty paragraph
                },
            ]
        }

        result = clean_docx_document(document)

        # Empty paragraphs should be removed
        assert len(result["paragraphs"]) == 1

    def test_clean_docx_document_structure(self, sample_docx_document):
        """Test that document structure is maintained"""
        result = clean_docx_document(sample_docx_document)

        # All original fields should be present
        assert "document_id" in result
        assert "source" in result
        assert "file_type" in result
        assert "language" in result


class TestCleanDocument:
    """Test suite for clean_document function"""

    def test_clean_pdf_document_type(self):
        """Test cleaning with PDF document type"""
        document = {
            "document_id": "pdf_test",
            "source": "test.pdf",
            "file_type": "pdf",
            "language": "en",
            "pages": [
                {
                    "page_number": 1,
                    "text": "   Content   \n\n\n"
                }
            ]
        }

        result = clean_document(document)

        assert result["file_type"] == "pdf"
        assert "Content" in result["pages"][0]["text"]

    def test_clean_docx_document_type(self):
        """Test cleaning with DOCX document type"""
        document = {
            "document_id": "docx_test",
            "source": "test.docx",
            "file_type": "docx",
            "language": "en",
            "paragraphs": [
                {
                    "paragraph_number": 1,
                    "text": "   Content   \t"
                }
            ]
        }

        result = clean_document(document)

        assert result["file_type"] == "docx"
        assert "Content" in result["paragraphs"][0]["text"]

    def test_clean_document_unsupported_type(self):
        """Test that unsupported document type raises ValueError"""
        document = {
            "document_id": "unknown",
            "file_type": "txt"
        }

        with pytest.raises(ValueError, match="Unsupported document type"):
            clean_document(document)

    def test_clean_document_missing_file_type(self):
        """Test that missing file_type raises ValueError"""
        document = {
            "document_id": "unknown"
        }

        with pytest.raises(ValueError):
            clean_document(document)
