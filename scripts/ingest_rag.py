"""
RAG (Retrieval-Augmented Generation) ingestion script.

Processes documents and indexes them for RAG retrieval:
- Ingests PDFs, TXT, Markdown files
- Chunks documents intelligently
- Generates embeddings
- Stores in vector database (Chroma)

Usage:
    python scripts/ingest_rag.py                      # Ingest all docs
    python scripts/ingest_rag.py --collection billing # Specific collection
    python scripts/ingest_rag.py --chunk-size 512     # Custom chunk size
    python scripts/ingest_rag.py --dry-run             # Preview ingestion
"""

import os
import json
import glob
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import asyncio


class Colors:
    """Terminal colors."""
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(msg: str) -> None:
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg: str) -> None:
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_warning(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


def print_info(msg: str) -> None:
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


class DocumentProcessor:
    """Process documents for RAG ingestion."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """Initialize processor."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def read_file(self, filepath: str) -> Optional[str]:
        """Read file content."""
        try:
            filepath = Path(filepath)
            
            if filepath.suffix == '.pdf':
                return self._read_pdf(filepath)
            elif filepath.suffix in ['.txt', '.md']:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                print_warning(f"Unsupported file type: {filepath.suffix}")
                return None
        
        except Exception as e:
            print_error(f"Failed to read {filepath}: {e}")
            return None
    
    def _read_pdf(self, filepath: Path) -> Optional[str]:
        """Read PDF file."""
        try:
            import PyPDF2
            text = []
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text())
            return '\n'.join(text)
        except ImportError:
            print_warning("PyPDF2 not installed. Install with: pip install PyPDF2")
            return None
        except Exception as e:
            print_error(f"Failed to read PDF {filepath}: {e}")
            return None
    
    def chunk_document(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split document into chunks."""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            if len(chunk_words) < 10:  # Skip very small chunks
                continue
            
            chunk_text = ' '.join(chunk_words)
            chunks.append({
                'content': chunk_text,
                'source': metadata['source'],
                'page': metadata.get('page', 0),
                'chunk_id': len(chunks),
            })
        
        return chunks
    
    def process_documents(self, directory: str, pattern: str = "**/*.*") -> List[Dict[str, Any]]:
        """Process all documents in directory."""
        documents = []
        doc_dir = Path(directory)
        
        if not doc_dir.exists():
            print_warning(f"Directory not found: {directory}")
            return documents
        
        files = list(doc_dir.glob(pattern))
        print_info(f"Found {len(files)} files")
        
        for filepath in files:
            if filepath.suffix not in ['.pdf', '.txt', '.md']:
                continue
            
            print_info(f"Processing: {filepath.name}")
            
            content = self.read_file(str(filepath))
            if not content:
                continue
            
            metadata = {
                'source': filepath.name,
                'path': str(filepath),
            }
            
            chunks = self.chunk_document(content, metadata)
            documents.extend(chunks)
            print_success(f"  Created {len(chunks)} chunks")
        
        return documents


class EmbeddingGenerator:
    """Generate embeddings for documents."""
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text."""
        try:
            import numpy as np
            # Placeholder: In production, use actual embedding model
            # Example: OpenAI, HuggingFace, or local model
            
            # For demo, create fake embedding
            hash_value = hash(text)
            np.random.seed(hash_value % (2**32))
            embedding = np.random.randn(384).tolist()  # 384-dim embedding
            return embedding
        
        except Exception as e:
            print_error(f"Failed to generate embedding: {e}")
            return None
    
    async def generate_embeddings_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate embeddings for batch of documents."""
        print_info("Generating embeddings...")
        
        for doc in documents:
            embedding = await self.generate_embedding(doc['content'])
            if embedding:
                doc['embedding'] = embedding
        
        return documents


class VectorStore:
    """Interface to vector database (Chroma)."""
    
    def __init__(self, collection_name: str = "billing_docs"):
        """Initialize vector store."""
        self.collection_name = collection_name
        self.client = None
    
    def connect(self) -> bool:
        """Connect to Chroma."""
        try:
            import chromadb
            self.client = chromadb.Client()
            print_success(f"Connected to Chroma")
            return True
        except ImportError:
            print_warning("chromadb not installed. Install with: pip install chromadb")
            return False
        except Exception as e:
            print_error(f"Failed to connect to Chroma: {e}")
            return False
    
    async def store_documents(
        self,
        documents: List[Dict[str, Any]],
        dry_run: bool = False
    ) -> int:
        """Store documents in vector store."""
        if dry_run:
            print_info(f"[DRY RUN] Would store {len(documents)} documents")
            for i, doc in enumerate(documents[:3], 1):
                print_info(f"  {i}. {doc['source']} - {doc['content'][:50]}...")
            if len(documents) > 3:
                print_info(f"  ... and {len(documents) - 3} more")
            return len(documents)
        
        if not self.client:
            print_error("Not connected to Chroma")
            return 0
        
        try:
            collection = self.client.get_or_create_collection(
                name=self.collection_name
            )
            
            # Prepare data for Chroma
            ids = [f"{doc['source']}_{doc['chunk_id']}" for doc in documents]
            embeddings = [doc.get('embedding') for doc in documents]
            metadatas = [
                {
                    'source': doc['source'],
                    'chunk_id': doc['chunk_id'],
                }
                for doc in documents
            ]
            documents_text = [doc['content'] for doc in documents]
            
            # Add to collection
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents_text
            )
            
            print_success(f"Stored {len(documents)} documents in {self.collection_name}")
            return len(documents)
        
        except Exception as e:
            print_error(f"Failed to store documents: {e}")
            return 0


class RAGIngestor:
    """Main RAG ingestion orchestrator."""
    
    def __init__(self, data_dir: str = "database", chunk_size: int = 500):
        """Initialize ingester."""
        self.data_dir = data_dir
        self.processor = DocumentProcessor(chunk_size=chunk_size)
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = None
    
    async def ingest(
        self,
        collection_name: str = "billing_docs",
        dry_run: bool = False
    ) -> bool:
        """Run full ingestion pipeline."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}RAG Ingestion Pipeline{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        
        # Step 1: Process documents
        print_info("Step 1: Processing documents...")
        documents = self.processor.process_documents(self.data_dir)
        
        if not documents:
            print_warning("No documents to ingest")
            return False
        
        print_success(f"Found {len(documents)} document chunks")
        
        # Step 2: Generate embeddings
        print_info("\nStep 2: Generating embeddings...")
        documents = await self.embedding_gen.generate_embeddings_batch(documents)
        print_success(f"Generated embeddings for {len(documents)} chunks")
        
        # Step 3: Store in vector database
        print_info("\nStep 3: Storing in vector database...")
        self.vector_store = VectorStore(collection_name)
        
        if not dry_run and not self.vector_store.connect():
            print_warning("Could not connect to vector database, using dry-run mode")
            dry_run = True
        
        stored = await self.vector_store.store_documents(documents, dry_run)
        
        # Summary
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        if dry_run:
            print(f"{Colors.YELLOW}DRY RUN: {stored} documents would be ingested{Colors.RESET}")
        else:
            print(f"{Colors.GREEN}Successfully ingested {stored} documents{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        
        return True


def create_sample_docs(output_dir: str = "database/sample_docs") -> None:
    """Create sample documents for testing."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Sample billing document
    billing_doc = """
    BILLING GUIDE
    
    How to Check Your Bill
    1. Log into your account
    2. Navigate to Billing section
    3. Select the month you want to view
    4. Download or view online
    
    Understanding Your Bill
    - Monthly Service Charge: Base plan cost
    - Additional Charges: Extra features used
    - Discounts: Applied promotions
    - Taxes: Government taxes
    
    Payment Methods
    - Credit Card
    - Debit Card
    - Bank Transfer
    - Mobile Wallet
    
    Due Dates
    Bill is due 15 days after issue date.
    Late payments may incur additional charges.
    """
    
    # Sample FAQ document
    faq_doc = """
    FREQUENTLY ASKED QUESTIONS
    
    Q: How can I upgrade my plan?
    A: Contact customer support or upgrade through your account dashboard.
    
    Q: What is the refund policy?
    A: Full refund within 30 days if you're not satisfied.
    
    Q: Do you offer technical support?
    A: Yes, 24/7 technical support available via phone, email, or chat.
    
    Q: How do I report an issue?
    A: Use the support portal or call our toll-free number.
    """
    
    with open(f"{output_dir}/billing_guide.txt", "w") as f:
        f.write(billing_doc)
    
    with open(f"{output_dir}/faq.txt", "w") as f:
        f.write(faq_doc)
    
    print_success(f"Created sample documents in {output_dir}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Ingest documents for RAG")
    parser.add_argument(
        "--data-dir",
        default="database",
        help="Directory containing documents (default: database)"
    )
    parser.add_argument(
        "--collection",
        default="billing_docs",
        help="Chroma collection name (default: billing_docs)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Chunk size in words (default: 500)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview ingestion without storing"
    )
    parser.add_argument(
        "--create-samples",
        action="store_true",
        help="Create sample documents for testing"
    )
    
    args = parser.parse_args()
    
    # Create sample documents if requested
    if args.create_samples:
        create_sample_docs()
    
    # Run ingestion
    ingester = RAGIngestor(
        data_dir=args.data_dir,
        chunk_size=args.chunk_size
    )
    
    success = asyncio.run(ingester.ingest(
        collection_name=args.collection,
        dry_run=args.dry_run
    ))
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
