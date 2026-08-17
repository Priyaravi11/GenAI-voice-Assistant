# RAG Tests - Quick Start Guide

## What's New
✅ **122 comprehensive tests** created for RAG modules  
✅ **All tests passing** (100% success rate)  
✅ **6 test files** covering embeddings, chunking, document loading, cleaning, vector store, and translation

## Quick Commands

### Run All New Tests
```bash
cd C:\PROJECTS\GenAI-voice-Assistant
python -m pytest rag/tests/test_*.py -v
```

### Run Individual Test Files
```bash
# Test embeddings module
python -m pytest rag/tests/test_embeddings.py -v

# Test chunking functionality
python -m pytest rag/tests/test_chunking.py -v

# Test document loading
python -m pytest rag/tests/test_document_loader.py -v

# Test text cleaning
python -m pytest rag/tests/test_cleaner.py -v

# Test vector store and retrieval
python -m pytest rag/tests/test_vector_store.py -v

# Test translation (future implementation template)
python -m pytest rag/tests/test_translation.py -v
```

### Run Specific Test Class
```bash
python -m pytest rag/tests/test_embeddings.py::TestEmbeddingModel -v
```

### Run Specific Test
```bash
python -m pytest rag/tests/test_chunking.py::TestSplitText::test_empty_text_returns_empty_list -v
```

### Run with Details
```bash
# Verbose with short traceback
python -m pytest rag/tests/ -v --tb=short

# Verbose with full traceback
python -m pytest rag/tests/ -v --tb=long

# Show print statements
python -m pytest rag/tests/ -v -s
```

## Test Organization

| Module | Tests | Focus |
|--------|-------|-------|
| **test_embeddings.py** | 13 | Text embedding generation and validation |
| **test_chunking.py** | 16 | Document chunking with overlap |
| **test_document_loader.py** | 20 | PDF/DOCX loading and language detection |
| **test_cleaner.py** | 24 | Text normalization and cleaning |
| **test_vector_store.py** | 25 | Vector store and retrieval operations |
| **test_translation.py** | 24 | Translation functionality (template) |

## Test Coverage

### Embeddings (13 tests)
- Model initialization
- Single and batch embedding
- Multilingual Unicode support
- Error handling
- Embedding properties

### Chunking (16 tests)
- Text splitting logic
- Chunk overlap handling
- Metadata preservation
- Paragraph grouping
- Large document handling

### Document Loading (20 tests)
- Language detection (en, ta, hi, te, ml)
- PDF extraction with page tracking
- DOCX extraction with paragraph tracking
- File validation
- Error handling

### Text Cleaning (24 tests)
- Line ending normalization
- Whitespace collapsing
- Empty line removal
- Unicode preservation
- Document-type specific cleaning

### Vector Store (25 tests)
- Client initialization
- Collection management
- Retriever functionality
- Query validation
- Result formatting

### Translation (24 tests)
- Language detection
- Query translation
- Response translation
- Code-switching handling
- Error scenarios

## Key Features

✅ **Comprehensive**: Covers normal cases, edge cases, and errors  
✅ **Multilingual**: Tests support English, Tamil, Hindi, Telugu, Malayalam  
✅ **Organized**: Logical grouping with clear naming  
✅ **Maintainable**: Reusable fixtures and utilities  
✅ **Well-documented**: Each test has clear purpose  

## Common Issues & Solutions

### Issue: Model Download on First Run
**Solution**: First test may take time to download embedding model
```bash
# The download happens automatically on first test run
# Subsequent runs will be much faster (cached model)
```

### Issue: Need to Install Dependencies
**Solution**: Install RAG requirements
```bash
pip install -r rag/requirements.txt
```

### Issue: Want to Skip Certain Tests
**Solution**: Use markers or patterns
```bash
# Skip slow tests
python -m pytest rag/tests/ -v -m "not slow"

# Run only embedding tests
python -m pytest rag/tests/test_embeddings.py -v
```

## Next Steps

1. **Run tests regularly** - Integrate into CI/CD pipeline
2. **Add more test data** - Expand test cases with more languages/domains
3. **Implement translation module** - Use test_translation.py as specification
4. **Monitor performance** - Track test execution time
5. **Expand coverage** - Add integration tests for full RAG pipeline

## Troubleshooting

### Tests taking too long?
- First embeddings test downloads model (~500MB)
- Subsequent runs are faster with cached model
- Check disk space: `C:\Users\{username}\.cache\huggingface\`

### Import errors?
```bash
# Verify PYTHONPATH includes project root
cd C:\PROJECTS\GenAI-voice-Assistant
python -c "import rag; print(rag.__file__)"
```

### Need to update tests?
- Edit relevant test file in `rag/tests/`
- Re-run with `python -m pytest rag/tests/ -v`
- All tests should remain independent

## Documentation

- Full details: See `TEST_SUMMARY.md`
- Implementation guide: See individual test file docstrings
- Requirements: See `rag/requirements.txt`
