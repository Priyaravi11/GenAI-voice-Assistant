import re
from typing import Dict, List


def clean_text(text: str) -> str:
    """
    Clean extracted document text while preserving
    multilingual Unicode characters.
    """

    if not text:
        return ""

    # Normalize Windows and old-style line endings.
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Replace tabs with spaces.
    text = text.replace("\t", " ")

    # Remove spaces at the beginning/end of each line.
    lines = [
        line.strip()
        for line in text.split("\n")
    ]

    # Remove completely empty lines.
    lines = [
        line
        for line in lines
        if line
    ]

    # Join lines temporarily.
    text = "\n".join(lines)

    # Replace multiple spaces with a single space.
    text = re.sub(r"[ ]{2,}", " ", text)

    # Normalize excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_pdf_document(document: Dict) -> Dict:
    """
    Clean all pages of a loaded PDF document.
    """

    cleaned_pages: List[Dict] = []

    for page in document.get("pages", []):

        cleaned_text = clean_text(
            page.get("text", "")
        )

        if cleaned_text:

            cleaned_pages.append(
                {
                    "page_number": page["page_number"],
                    "text": cleaned_text,
                }
            )

    cleaned_document = document.copy()

    cleaned_document["pages"] = cleaned_pages

    return cleaned_document


def clean_docx_document(document: Dict) -> Dict:
    """
    Clean all paragraphs of a loaded DOCX document.
    """

    cleaned_paragraphs: List[Dict] = []

    for paragraph in document.get("paragraphs", []):

        cleaned_text = clean_text(
            paragraph.get("text", "")
        )

        if cleaned_text:

            cleaned_paragraphs.append(
                {
                    "paragraph_number": paragraph[
                        "paragraph_number"
                    ],
                    "text": cleaned_text,
                }
            )

    cleaned_document = document.copy()

    cleaned_document["paragraphs"] = cleaned_paragraphs

    return cleaned_document


def clean_document(document: Dict) -> Dict:
    """
    Clean a loaded document based on its file type.
    """

    file_type = document.get("file_type")

    if file_type == "pdf":
        return clean_pdf_document(document)

    if file_type == "docx":
        return clean_docx_document(document)

    raise ValueError(
        f"Unsupported document type: {file_type}"
    )