from pathlib import Path
from typing import Dict, List

import pymupdf
from docx import Document


SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

SUPPORTED_LANGUAGES = {"en", "ta", "hi", "te", "ml"}


def detect_language_from_path(file_path: Path) -> str:
    """
    Detect language based on the parent folder name.

    Expected structure:

        data/raw/en/file.pdf
        data/raw/ta/file.pdf
        data/raw/hi/file.pdf
        data/raw/te/file.pdf
        data/raw/ml/file.pdf
    """

    language = file_path.parent.name.lower()

    if language in SUPPORTED_LANGUAGES:
        return language

    return "unknown"


def load_pdf(file_path: Path) -> Dict:
    """
    Extract text from a PDF while preserving page information.
    """

    document = pymupdf.open(file_path)

    pages: List[Dict] = []

    for page_number, page in enumerate(document, start=1):

        text = page.get_text().strip()

        if text:
            pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                }
            )

    total_pages = len(document)

    document.close()

    return {
        "document_id": file_path.stem,
        "source": file_path.name,
        "file_type": "pdf",
        "language": detect_language_from_path(file_path),
        "total_pages": total_pages,
        "pages": pages,
    }


def load_docx(file_path: Path) -> Dict:
    """
    Extract text from a DOCX document.

    DOCX does not have reliable page information
    without rendering the document, so we store
    paragraph-level content for now.
    """

    document = Document(file_path)

    paragraphs: List[Dict] = []

    for paragraph_number, paragraph in enumerate(
        document.paragraphs,
        start=1,
    ):

        text = paragraph.text.strip()

        if text:
            paragraphs.append(
                {
                    "paragraph_number": paragraph_number,
                    "text": text,
                }
            )

    return {
        "document_id": file_path.stem,
        "source": file_path.name,
        "file_type": "docx",
        "language": detect_language_from_path(file_path),
        "total_pages": None,
        "paragraphs": paragraphs,
    }


def load_document(file_path: str) -> Dict:
    """
    Load a supported document based on its file extension.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            f"Supported types: {SUPPORTED_EXTENSIONS}"
        )

    if extension == ".pdf":
        return load_pdf(path)

    if extension == ".docx":
        return load_docx(path)

    raise ValueError(
        f"Unsupported document: {file_path}"
    )