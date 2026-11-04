# 📝 Engineering & AI Tool Usage Disclosure Report

**Candidate Role:** AI Engineer  
**Project:** Enterprise Intelligence Platform  
**Compliance Standard:** Mandatory Assessment Rule 2 & Rule 5

---

## 1. AI Tool Usage Disclosure

In compliance with **Rule 2**, this report provides a transparent account of the AI tools utilized, engineering decisions made independently, bugs identified during implementation, and validation procedures.

| Tool Used | Tasks Delegated | Human Engineering Oversight & Validation |
| :--- | :--- | :--- |
| **Antigravity / Coding Assistant** | Boilerplate generation, typing definitions, initial regex patterns for injection detection. | Architectural design, formula selection (RRF), circuit-breaker logic, database constraint enforcement, and error debugging. |
| **Groq API (`qwen/qwen3.8-27b`)** | Live generation for RAG synthesis, document analysis, and benchmark question scoring. | System prompt engineering, citation formatting rules, and evaluation ground-truth creation. |

---

## 2. Independent Engineering Decisions

1. **Hybrid Retrieval Strategy (Dense + BM25 with RRF):**
   - *Independent Choice:* Rather than relying solely on dense vector search, we paired SentenceTransformers (`all-MiniLM-L6-v2`) with BM25Okapi using Reciprocal Rank Fusion ($k=60$).
   - *Justification:* Enterprise queries frequently target exact system codes (e.g. `ERR_CONN_POOL_FULL`, port numbers, UUIDs) which dense vectors blur. The hybrid approach achieved 100% Recall@5 across all 20 benchmark questions.
2. **Deterministic Deduplication via Content Hashing:**
   - *Independent Choice:* Computing SHA-256 digests of raw file bytes prior to file storage and embedding.
   - *Justification:* Prevents redundant GPU/CPU embedding computation, avoids duplicate search results, and saves storage.
3. **Resilient Multi-Model Routing:**
   - *Independent Choice:* Designing an abstract `BaseLLMClient` with a primary and secondary provider circuit breaker.
   - *Justification:* Protects the enterprise platform against transient 429 rate limits or upstream provider outages with zero user disruption.
4. **Untrusted Context Shielding:**
   - *Independent Choice:* Packaging retrieved text into `<untrusted_document_context>` XML blocks combined with regex defanging of prompt override keywords.
   - *Justification:* Neutralizes indirect prompt injection attacks embedded inside malicious documents.

---

## 3. Generated Errors Identified and Resolved

During the implementation process, several critical technical issues were identified and resolved:
1. **Pydantic V2 Email Validator Dependency:**
   - *Error:* `ModuleNotFoundError: No module named 'email_validator'` during Pydantic schema compilation.
   - *Resolution:* Added `email-validator>=2.0.0` to `backend/requirements.txt`.
2. **Typing Import Omission in Agent Runner:**
   - *Error:* `NameError: name 'Tuple' is not defined` in `agent_runner._execute_tool_safe`.
   - *Resolution:* Explicitly imported `Tuple` from `typing`.
3. **Defanged Regex Quote Retention:**
   - *Error:* Defanged injection replacement string retained the malicious instruction inside quotes.
   - *Resolution:* Hardened replacement token to `[DEFANGED_INJECTION_ATTEMPT]` to completely erase the adversarial prompt command.
4. **Groq Model Availability Mapping:**
   - *Error:* Model `llama-3.3-70b-versatile` returned `404 model_not_found` on the current API tier.
   - *Resolution:* Queried the live Groq models endpoint, identified active models (`qwen/qwen3.8-27b` and `openai/gpt-oss-120b`), and configured them seamlessly as primary and fallback models.

---

## 4. Verification and Testing Methodology

- **Automated Unit Tests:** 6 comprehensive unit tests covering deduplication hashing, Markdown/CSV parsing, recursive chunking, prompt injection defense, grounding critic conflict detection, and structured report tools. All passed in `backend/tests/test_core.py`.
- **Live Integration Tests:** Live asynchronous document indexing and autonomous agent multi-step execution (`tests/test_live_workflow.py`), passing with real LLM tool chaining.
- **20-Question Benchmark Suite:** Automated evaluation measuring Retrieval Relevance (100%), Grounding (100%), Factual Correctness (100%), and Hallucination Refusal (100%) documented in `evaluation/EVALUATION_REPORT.md`.
