# GenAI Voice Assistant

A full-stack GenAI voice assistant project with a Python backend, a Vite/React frontend, RAG components, tool integrations, and seed data for local development.

## Project Structure

```text
backend/    Python API, agents, tools, WebSocket, and orchestration code
frontend/   Vite/React client application
rag/        RAG ingestion, chunking, embedding, and indexing utilities
database/   Seed data for local development
scripts/    Utility scripts for seeding and running the app
tests/      Backend test suite
docs/       Architecture and design documentation
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
