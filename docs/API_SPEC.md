# 🔌 REST API Specification & Swagger Documentation

The platform provides a fully documented OpenAPI 3.1 REST API accessible interactively at `/docs` (Swagger UI) and `/redoc`.

All protected routes accept a standard Bearer JWT token in the `Authorization` header:
`Authorization: Bearer <jwt_access_token>`

---

## API Endpoints Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/health` | Service health, models, and provider status | No |
| `POST` | `/api/v1/auth/register` | Register new user account | No |
| `POST` | `/api/v1/auth/login` | Login and receive Bearer JWT token | No |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile | Yes |
| `POST` | `/api/v1/documents/upload` | Upload PDF/CSV/MD/TXT with SHA-256 deduplication | Optional |
| `GET` | `/api/v1/documents` | List all ingested documents and statuses | Optional |
| `GET` | `/api/v1/documents/{id}` | Inspect document chunks and processing status | Optional |
| `DELETE` | `/api/v1/documents/{id}` | Delete document, vectors, and BM25 index | Optional |
| `POST` | `/api/v1/chat/query` | Execute Hybrid RAG Q&A with citations | Optional |
| `GET` | `/api/v1/chat/conversations` | List conversation sessions | Optional |
| `GET` | `/api/v1/chat/conversations/{id}/messages` | Get message history and citations | Optional |
| `POST` | `/api/v1/agent/run` | Execute multi-step autonomous agent workflow | Optional |
| `GET` | `/api/v1/analytics/summary` | Real-time KPI summary (tokens, cost, latency) | Optional |
| `GET` | `/api/v1/analytics/logs` | Audit trail of query telemetry logs | Optional |

---

## Key Request & Response Examples

### 1. Document Upload (`POST /api/v1/documents/upload`)
- **Content-Type:** `multipart/form-data`
- **Response (`202 Accepted`):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "incident_postmortem_db_pool.txt",
  "status": "PENDING",
  "message": "File accepted for asynchronous processing.",
  "is_duplicate": false
}
```

### 2. Hybrid RAG Query (`POST /api/v1/chat/query`)
- **Request Body:**
```json
{
  "query": "What was the primary root cause of outage INC-89421?",
  "conversation_id": null,
  "hybrid_search": true
}
```
- **Response (`200 OK`):**
```json
{
  "conversation_id": "c7a8...",
  "message_id": "m9b1...",
  "answer": "The primary root cause of outage INC-89421 was that the PostgreSQL connection pool was capped at 120 connections, which was exhausted by a 400% surge from a batch indexing job [Doc: incident_postmortem_db_pool.txt, Page: 3].",
  "citations": [
    {
      "document_id": "doc_inc_2",
      "document_name": "incident_postmortem_db_pool.txt",
      "page_or_row": 3,
      "chunk_id": "doc_inc_2_c2",
      "excerpt": "ROOT CAUSE ANALYSIS:\n1. Primary Root Cause: The primary PostgreSQL connection pool...",
      "similarity_score": 0.8841
    }
  ],
  "conflicts_detected": [],
  "is_grounded": true,
  "model_used": "qwen/qwen3.8-27b",
  "provider_used": "groq",
  "is_fallback": false,
  "tokens_prompt": 1284,
  "tokens_completion": 218,
  "total_tokens": 1502,
  "latency_ms": 1367,
  "created_at": "2026-11-04T09:30:00Z"
}
```

### 3. Autonomous Agent Execution (`POST /api/v1/agent/run`)
- **Request Body:**
```json
{
  "task": "Analyze our internal technical documentation and identify the most common reasons for system failures. Provide evidence from the documents and recommend possible solutions.",
  "max_steps": 6
}
```
- **Response (`200 OK`):** Returns synthesized output, structured markdown incident report, and full `steps` trace showing every tool invoked, arguments, outputs, and latencies.
