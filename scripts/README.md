# GenAI Voice Assistant - Scripts Guide

Utility scripts for development, testing, and data management.

## Scripts Overview

### 1. run_dev.py - Development Server Launcher

Starts backend and frontend development servers with live reloading.

**Features:**
- Automatic environment checks
- Python venv detection
- Dependency verification
- Hot reload for both services
- Graceful shutdown

**Usage:**
```bash
# Start both servers
python scripts/run_dev.py

# Backend only
python scripts/run_dev.py --backend-only

# Frontend only
python scripts/run_dev.py --frontend-only

# Custom backend port
python scripts/run_dev.py --port 8001

# Disable auto-reload
python scripts/run_dev.py --no-reload

# Skip environment checks
python scripts/run_dev.py --skip-checks
```

**Output:**
```
============================================================
GenAI Voice Assistant - Development Server
============================================================

✓ Python 3.13 ✓
✓ .env file found ✓
✓ Virtual environment activated ✓
✓ Backend dependencies installed ✓
✓ Frontend dependencies installed ✓

============================================================
Backend Server (port 8000)
============================================================
ℹ Backend server starting...
✓ Backend server started (PID: 12345)

✓ Server 127.0.0.1:8000 is ready

[BACKEND] INFO:     Uvicorn running on http://0.0.0.0:8000

============================================================
Development Servers Running
============================================================
ℹ Backend:  http://localhost:8000
ℹ API Docs: http://localhost:8000/docs
ℹ Frontend: http://localhost:5173
```

**What it checks:**
- Python version (3.11+)
- Virtual environment activation
- `.env` file exists
- Backend dependencies installed
- Frontend dependencies installed

---

### 2. seed_mongodb.py - Database Seeding

Populates MongoDB with initial test data.

**Features:**
- Sample customers with profiles
- Billing information
- Call records
- Agent profiles
- Escalation cases
- Dry-run mode
- Selective seeding

**Usage:**
```bash
# Seed all data
python scripts/seed_mongodb.py

# Dry-run (preview without inserting)
python scripts/seed_mongodb.py --dry-run

# Clear collections first
python scripts/seed_mongodb.py --clear

# Seed only customers
python scripts/seed_mongodb.py --customers-only

# Seed only agents
python scripts/seed_mongodb.py --agents-only

# Custom MongoDB URI
python scripts/seed_mongodb.py --mongodb-uri mongodb://user:pass@host:27017
```

**Sample Data:**

**Customers (4 records)**
- C001: Rajesh Kumar (Premium, English)
- C002: Priya Sharma (Standard, Hindi)
- C003: Arjun Patel (Premium, English)
- C004: Anjali Singh (Standard, Tamil)

**Billing (3 records)**
- Monthly bills for customers C001, C002, C003
- Various charges and due dates

**Calls (3 records)**
- Billing inquiry, plan upgrade, technical support
- Mix of AI and human agents

**Agents (3 profiles)**
- Support specialists with queue management
- Different availability statuses

**Escalations (2 cases)**
- High and urgent priority cases
- Different reasons and statuses

**Output:**
```
✓ Connected to MongoDB: mongodb://localhost:27017
ℹ Seeding customers...
✓ Inserted 4 documents into customers
ℹ Seeding billing data...
✓ Inserted 3 documents into billing
ℹ Seeding call records...
✓ Inserted 3 documents into calls
ℹ Seeding agent profiles...
✓ Inserted 3 documents into agents
ℹ Seeding escalation cases...
✓ Inserted 2 documents into escalations

============================================================
Successfully inserted 18 documents
============================================================
```

---

### 3. ingest_rag.py - RAG Document Ingestion

Processes and indexes documents for RAG retrieval.

**Features:**
- Multi-format support (PDF, TXT, Markdown)
- Intelligent document chunking
- Embedding generation
- Chroma vector database integration
- Dry-run mode
- Sample document generation

**Usage:**
```bash
# Ingest all documents
python scripts/ingest_rag.py

# Dry-run (preview)
python scripts/ingest_rag.py --dry-run

# Custom collection name
python scripts/ingest_rag.py --collection billing_docs

# Custom chunk size (default: 500 words)
python scripts/ingest_rag.py --chunk-size 512

# Custom data directory
python scripts/ingest_rag.py --data-dir ./documents

# Create sample documents for testing
python scripts/ingest_rag.py --create-samples
```

**Supported File Types:**
- `.pdf` - PDF documents
- `.txt` - Text files
- `.md` - Markdown files

**Processing Pipeline:**
1. Read documents from directory
2. Split into chunks (with overlap)
3. Generate embeddings for each chunk
4. Store in Chroma vector database

**Output:**
```
============================================================
RAG Ingestion Pipeline
============================================================

ℹ Step 1: Processing documents...
ℹ Found 5 files
ℹ Processing: billing_guide.txt
✓   Created 12 chunks
ℹ Processing: faq.txt
✓   Created 8 chunks

ℹ Step 2: Generating embeddings...
✓ Generated embeddings for 20 chunks

ℹ Step 3: Storing in vector database...
✓ Connected to Chroma
✓ Stored 20 documents in billing_docs

============================================================
Successfully ingested 20 documents
============================================================
```

---

### 4. test_api.py - API Endpoint Testing

Tests core API endpoints and WebSocket communication.

**Features:**
- Health check endpoint
- Query processing endpoint
- Call logs retrieval
- WebSocket connection
- Multi-message handling
- Customizable base URL

**Usage:**
```bash
# Run all tests
python scripts/test_api.py

# Health check only
python scripts/test_api.py --health

# Custom server URL
python scripts/test_api.py --url http://localhost:8001

# WebSocket tests only
python scripts/test_api.py --websocket
```

**Tests:**
1. **Health Check** - Verify server is running
2. **Query Endpoint** - Process natural language queries
3. **Call Logs** - Retrieve call history
4. **WebSocket Connection** - Real-time communication
5. **Multiple Messages** - Concurrent query handling

**Output:**
```
============================================================
GenAI Voice Assistant - API Tests
============================================================

============================================================
Testing Health Endpoint
============================================================
✓ Health check passed
ℹ Response: {'status': 'ok', 'version': '1.0.0'}

============================================================
Testing Query Endpoint
============================================================
ℹ Sending query: What is my current bill?
✓ Query processed successfully
ℹ Response: Your current bill is $150.00

============================================================
Test Summary
============================================================
✓ Health Check: PASS
✓ Query Endpoint: PASS
✓ Call Logs: PASS
✓ WebSocket Connection: PASS
✓ WebSocket Multiple Messages: PASS

✓ Passed: 5/5
```

---

## Quick Start

### 1. Initial Setup

```bash
# Navigate to project
cd C:\PROJECTS\GenAI-voice-Assistant

# Activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Seed Database

```bash
# Seed MongoDB with test data
python scripts/seed_mongodb.py --clear
```

### 3. Ingest Documents

```bash
# Create sample documents
python scripts/ingest_rag.py --create-samples

# Ingest into RAG
python scripts/ingest_rag.py
```

### 4. Start Development

```bash
# Start both servers
python scripts/run_dev.py
```

### 5. Test API

```bash
# In another terminal
python scripts/test_api.py
```

---

## Common Tasks

### Task 1: Full Local Development Setup

```bash
# 1. Create environment
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 3. Create .env file
cp .env.example .env
# Edit .env with your configuration

# 4. Seed database
python scripts/seed_mongodb.py --clear

# 5. Ingest RAG documents
python scripts/ingest_rag.py --create-samples

# 6. Start development servers
python scripts/run_dev.py

# 7. In another terminal, test API
python scripts/test_api.py
```

### Task 2: Quick Backend Testing

```bash
# Start backend only
python scripts/run_dev.py --backend-only

# Test endpoints
python scripts/test_api.py --health
python scripts/test_api.py --url http://localhost:8000
```

### Task 3: Database Refresh

```bash
# Clear and reseed database
python scripts/seed_mongodb.py --clear

# Reseed with dry-run first
python scripts/seed_mongodb.py --dry-run
python scripts/seed_mongodb.py
```

### Task 4: New Document Ingestion

```bash
# Place documents in database/docs/

# Ingest with dry-run first
python scripts/ingest_rag.py --dry-run

# Ingest into specific collection
python scripts/ingest_rag.py --collection custom_collection
```

---

## Environment Variables

Required in `.env` file:

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=genai_voice_assistant

# Gemini API
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-1.5-pro

# Server
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

# Chroma
CHROMA_COLLECTION=billing_docs
```

---

## Troubleshooting

### Issue: "Virtual environment not activated"
```bash
# Activate venv
venv\Scripts\activate
```

### Issue: "Module not found"
```bash
# Install dependencies
pip install -r requirements.txt
```

### Issue: "MongoDB connection failed"
```bash
# Check MongoDB is running
# On Windows, start MongoDB service:
# services.msc → MongoDB Server

# Or start locally:
mongod --dbpath C:\data\db
```

### Issue: "Port already in use"
```bash
# Use custom port
python scripts/run_dev.py --port 8001

# Or kill process using port
# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue: "WebSocket test fails"
```bash
# Make sure backend is running
python scripts/run_dev.py --backend-only

# Test health first
python scripts/test_api.py --health

# Then test websocket
python scripts/test_api.py --websocket
```

---

## Dependencies

Scripts require:
- Python 3.11+
- httpx (for HTTP testing)
- websockets (for WebSocket testing)
- motor (for async MongoDB)
- chromadb (for RAG)
- PyPDF2 (for PDF reading)

Install with:
```bash
pip install -r requirements.txt
```

---

## File Locations

```
scripts/
├── __init__.py           # Package init
├── run_dev.py            # Development server (367 lines)
├── seed_mongodb.py       # Database seeding (427 lines)
├── ingest_rag.py         # RAG ingestion (422 lines)
├── test_api.py           # API testing (322 lines)
└── README.md             # This file
```

---

## Additional Resources

- [Project README](../README.md)
- [Backend Documentation](../docs/)
- [API Documentation](../backend/app/api/)
- [Test Suite](../tests/)

---

**Last Updated**: August 16, 2026
**Maintained By**: GenAI Voice Assistant Team
