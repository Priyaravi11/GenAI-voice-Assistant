# GenAI Voice Assistant

A full-stack multilingual telecom voice assistant. The project follows the architecture in the supplied pipeline image: React captures the call UI and audio stream, FastAPI handles WebSocket traffic, Gemini Live generates voice responses, RAG retrieves policy/FAQ/plan/technical knowledge from ChromaDB, MongoDB-backed tools fetch customer data, and escalation routes complex cases to a human-agent queue.

## Project Structure

```text
backend/      FastAPI API, WebSocket, Gemini Live, orchestration, agents, and tool registry
frontend/     Vite/React voice UI, language selector, transcript, and call controls
rag/          RAG ingestion, embeddings, retrieval, context assembly, and ChromaDB client
tools/        Telecom tool implementations used by backend/app/tools.py
scripts/      Local setup helpers for MongoDB seeding, RAG ingestion, and dev startup
tests/        Backend and RAG test suite
docs/         Architecture, API contract, RAG, tool, Gemini Live, and escalation docs
```

## Requirements

- Python 3.11+
- Node.js 20+
- Docker Desktop, optional for containerized services

## Setup

Create a local environment file:

```bash
cp .env.example .env
```

Update these values in `.env`:

```env
GEMINI_API_KEY=your_real_google_ai_studio_key
GEMINI_LIVE_MODEL=gemini-3.1-flash-live-preview
GEMINI_TEXT_MODELS=gemini-2.5-flash,gemini-2.0-flash
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=telecom_db
CHROMA_PATH=rag/data/chroma
CHROMA_COLLECTION=telecom_knowledge
FRONTEND_URL=http://localhost:5173
```

Install Python dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

Seed local data for the tool path:

```bash
python scripts/seed_mongodb.py --clear
```

Build the RAG index for the knowledge path:

```bash
python scripts/ingest_rag.py
```

## Run Locally

Start the backend:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Start the frontend:

```bash
cd frontend
npm run dev
```

## Docker

Start local services:

```bash
docker compose up --build
```

## Tests

Run the backend test suite:

```bash
pytest tests
```

## Notes

Do not commit real API keys, tokens, database passwords, or customer data. Use `.env.example` as the template for required configuration.
