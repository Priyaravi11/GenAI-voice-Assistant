import csv
from pathlib import Path

from rag.embeddings.embedding_model import EmbeddingModel
from rag.vector_store.collection import get_collection


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CSV_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "knowledge_base"
    / "customer_knowledge_base.csv"
)


# ============================================================
# LOAD CSV
# ============================================================

def load_knowledge_base(csv_file):
    """
    Load customer knowledge-base records from CSV.
    """

    records = []

    with open(
        csv_file,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "customer_id",
            "query",
            "solution",
            "category"
        }

        if not required_columns.issubset(reader.fieldnames):
            raise ValueError(
                f"CSV must contain columns: {required_columns}"
            )

        for row in reader:

            customer_id = row["customer_id"].strip()
            query = row["query"].strip()
            solution = row["solution"].strip()
            category = row["category"].strip().lower()

            if not query or not solution:
                continue

            records.append(
                {
                    "customer_id": customer_id,
                    "query": query,
                    "solution": solution,
                    "category": category
                }
            )

    return records


# ============================================================
# MAIN INDEXING FUNCTION
# ============================================================

def build_index():

    print("=" * 60)
    print("CUSTOMER CARE RAG - KNOWLEDGE BASE INDEXING")
    print("=" * 60)

    # --------------------------------------------------------
    # Check CSV
    # --------------------------------------------------------

    if not CSV_FILE.exists():

        raise FileNotFoundError(
            f"Knowledge base not found:\n{CSV_FILE}"
        )

    print(f"\nKnowledge base: {CSV_FILE}")

    # --------------------------------------------------------
    # Load records
    # --------------------------------------------------------

    records = load_knowledge_base(CSV_FILE)

    print(f"Loaded records: {len(records)}")

    if not records:
        raise ValueError(
            "No valid records found in the knowledge base."
        )

    # --------------------------------------------------------
    # Load embedding model
    # --------------------------------------------------------

    print("\nLoading embedding model...")

    embedding_model = EmbeddingModel()

    print("Embedding model ready.")

    # --------------------------------------------------------
    # Get ChromaDB collection
    # --------------------------------------------------------

    collection = get_collection()

    print(
        f"\nChromaDB collection: {collection.name}"
    )

    print(
        f"Existing records: {collection.count()}"
    )

    # --------------------------------------------------------
    # Prepare data
    # --------------------------------------------------------

    ids = []
    documents = []
    metadatas = []
    embeddings = []

    print("\nGenerating embeddings...")

    for index, record in enumerate(records, start=1):

        # ----------------------------------------------------
        # Document text
        # ----------------------------------------------------

        document_text = (
            f"Customer Query: {record['query']}\n\n"
            f"Solution: {record['solution']}"
        )

        # ----------------------------------------------------
        # Unique ChromaDB ID
        # ----------------------------------------------------

        chunk_id = (
            f"{record['category']}"
            f"_{record['customer_id']}"
        )

        # ----------------------------------------------------
        # Generate embedding
        # ----------------------------------------------------

        vector = embedding_model.embed_text(
            document_text
        )

        # ----------------------------------------------------
        # Store values
        # ----------------------------------------------------

        ids.append(chunk_id)

        documents.append(document_text)

        metadatas.append(
            {
                "customer_id": record["customer_id"],
                "category": record["category"]
            }
        )

        embeddings.append(vector)

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if index % 25 == 0 or index == len(records):

            print(
                f"Processed {index}/{len(records)}"
            )

    # --------------------------------------------------------
    # Store in ChromaDB
    # --------------------------------------------------------

    print("\nStoring records in ChromaDB...")

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )

    # --------------------------------------------------------
    # Final information
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("INDEXING COMPLETED")
    print("=" * 60)

    print(
        f"Records processed : {len(records)}"
    )

    print(
        f"Records in ChromaDB: {collection.count()}"
    )

    print(
        f"Embedding dimension: "
        f"{embedding_model.get_dimension()}"
    )

    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    build_index()