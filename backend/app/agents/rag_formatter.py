from typing import Any, Optional


def build_response_from_rag(rag_context: Any) -> Optional[str]:
    documents = extract_rag_documents(rag_context)

    for document in documents:
        content = document.get("content") if isinstance(document, dict) else str(document)
        solution = extract_solution(content)
        if solution:
            return solution

    if documents:
        first_document = documents[0]
        content = (
            first_document.get("content")
            if isinstance(first_document, dict)
            else str(first_document)
        )
        return clean_rag_content(content)

    return None


def extract_rag_documents(rag_context: Any) -> list:
    if isinstance(rag_context, dict):
        retrieved_context = rag_context.get("retrieved_context")
        if isinstance(retrieved_context, list):
            return retrieved_context

        documents = rag_context.get("documents")
        if isinstance(documents, list):
            return documents

    if isinstance(rag_context, list):
        return rag_context

    return []


def extract_solution(content: Any) -> Optional[str]:
    if not content:
        return None

    text = str(content).strip()
    marker = "Solution:"

    if marker not in text:
        return None

    solution = text.split(marker, 1)[1].strip()
    return clean_rag_content(solution)


def clean_rag_content(content: Any) -> str:
    text = str(content).strip()

    if "\n\nCustomer Query:" in text:
        text = text.split("\n\nCustomer Query:", 1)[0].strip()

    if text.lower().startswith("customer query:") and "Solution:" in text:
        text = text.split("Solution:", 1)[1].strip()

    return text
