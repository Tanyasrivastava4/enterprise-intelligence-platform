# CLAUDE.md — Agent & Developer Guide

## Project Overview
Enterprise Intelligence Platform: A production-ready AI product with Hybrid RAG (Dense + BM25 + RRF), multi-model fallback, autonomous agent workflows (Knowledge Base Search, Document Analysis, Report Generation), and full observability.

## Repository Layout
- `backend/app/`: FastAPI application
  - `api/`: Route handlers (`auth`, `documents`, `chat`, `agent`, `analytics`)
  - `core/`: Configurations, database setup, JWT security
  - `models/`: SQLAlchemy async ORM models
  - `schemas/`: Pydantic validation schemas
  - `services/`: Ingestion, retrieval, LLM router, agent runner, and guardrails
- `frontend/`: React 18 + Vite + Tailwind CSS dashboard
- `evaluation/`: 20-question benchmark dataset & automated test harness
- `sample_data/`: Enterprise test documents (PDF, CSV, MD, TXT)
- `docs/`: Architecture, database schema, and live evaluation guides

## Key Developer Commands

### Backend Setup & Execution
```bash
# Activate environment
source venv/bin/activate

# Run backend API server with hot reload
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run test suite
PYTHONPATH=. pytest tests/test_core.py -v
PYTHONPATH=. pytest tests/test_live_workflow.py -v
```

### Frontend Build & Development
```bash
cd frontend
npm install
npm run dev     # Starts Vite dev server on :5173
npm run build   # Compiles production assets into dist/
```

### Run Benchmark Evaluation
```bash
cd evaluation
python run_eval.py
```

## Architectural Guidelines & Conventions
1. **Never commit actual API keys or secrets.** Use `.env` backed by `.env.example`.
2. **Type Safety:** Always validate tool inputs with Pydantic `BaseModel`.
3. **Retrieval Integrity:** Always attach citations `{document_name, page_or_row, chunk_id}` to generated answers.
4. **Idempotency:** Never re-index identical documents; use SHA-256 deduplication.
5. **Defense-in-Depth:** Wrap untrusted document excerpts inside `<untrusted_document_context>` XML boundaries.
