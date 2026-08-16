from typing import List, Dict


# Maximum number of characters allowed in one chunk
MAX_CHUNK_SIZE = 800

# Number of characters repeated between chunks
CHUNK_OVERLAP = 100


def split_text(text: str) -> List[str]:
    """
    Split long text into overlapping chunks.
    """

    if not text or not text.strip():
        return []

    text = text.strip()

    # If the text is already small enough,
    # keep it as one chunk.
    if len(text) <= MAX_CHUNK_SIZE:
        return [text]

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(
            start + MAX_CHUNK_SIZE,
            text_length
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - CHUNK_OVERLAP

    return chunks


def chunk_document(document: Dict) -> List[Dict]:
    """
    Convert a cleaned document into RAG chunks.

    Related paragraphs are grouped together until
    MAX_CHUNK_SIZE is reached.
    """

    chunks = []

    current_texts = []
    current_paragraphs = []

    chunk_number = 1

    paragraphs = document.get("paragraphs", [])

    for paragraph in paragraphs:

        text = paragraph.get("text", "").strip()

        if not text:
            continue

        # Try adding the paragraph to the current chunk
        candidate_texts = current_texts + [text]

        candidate_text = "\n\n".join(candidate_texts)

        if (
            current_texts
            and len(candidate_text) > MAX_CHUNK_SIZE
        ):
            # Save current chunk
            chunks.append(
                _create_chunk(
                    document=document,
                    texts=current_texts,
                    paragraphs=current_paragraphs,
                    chunk_number=chunk_number
                )
            )

            chunk_number += 1

            # Start a new chunk with current paragraph
            current_texts = [text]
            current_paragraphs = [paragraph]

        else:
            current_texts.append(text)
            current_paragraphs.append(paragraph)

    # Add remaining paragraphs
    if current_texts:

        chunks.append(
            _create_chunk(
                document=document,
                texts=current_texts,
                paragraphs=current_paragraphs,
                chunk_number=chunk_number
            )
        )

    return chunks


def _create_chunk(
    document: Dict,
    texts: List[str],
    paragraphs: List[Dict],
    chunk_number: int
) -> Dict:
    """
    Create one structured RAG chunk.
    """

    text = "\n\n".join(texts)

    first_paragraph = paragraphs[0]

    metadata = {
      "document_id": document["document_id"],
      "source": document["source"],
      "file_type": document["file_type"],
      "language": document["language"],
      "category": document.get("category"),
      "subcategory": document.get("subcategory"),
      "page_number": first_paragraph.get("page_number"),
      "paragraph_start": paragraphs[0].get(
        "paragraph_number"
      ),
      "paragraph_end": paragraphs[-1].get(
        "paragraph_number"
      ),
    }
    return {
        "chunk_id": (
            f"{document['document_id']}"
            f"_chunk_{chunk_number}"
        ),
        "text": text,
        "metadata": metadata,
    }