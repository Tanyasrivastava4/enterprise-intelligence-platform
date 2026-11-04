# 🎥 5–10 Minute Demo Video Walkthrough Script

Use this exact structure when recording the 5–10 minute demonstration video required in Section 9 of the assessment brief.

---

## ⏱️ Timeline & Step-by-Step Script

### Minute 0:00 – 1:30 | Introduction & Architectural Overview
- **Visual:** Open browser to `http://localhost:8000` showing the clean Enterprise Intelligence Platform UI and architecture diagram in `docs/ARCHITECTURE.md`.
- **Narration:**
  > *"Hi everyone, this is my technical submission for the AI Engineer role at Appagentix / One GTM Lab. Today I'm presenting our AI-Powered Enterprise Intelligence Platform, built end-to-end to ingest complex corporate documents, answer technical inquiries with verified citations, and execute multi-step autonomous agent tasks.
  > The architecture is built with a FastAPI backend, an interactive React 18 dashboard, SentenceTransformers and ChromaDB for dense vector search, BM25Okapi for sparse keyword search combined via Reciprocal Rank Fusion, and a resilient multi-model router with automatic fallback."*

---

### Minute 1:30 – 3:30 | Module A: Document Intelligence Pipeline & Deduplication
- **Visual:** Navigate to the **"Document Intelligence"** tab.
- **Actions:**
  1. Drag and drop `sample_data/architecture_specs.md` and `sample_data/incident_postmortem_db_pool.txt`.
  2. Show the processing badges transition from `PENDING` $\to$ `INDEXED`.
  3. Drag and drop `architecture_specs.md` **again**.
- **Narration:**
  > *"Here in the Document Intelligence Center, we support PDF, CSV, Markdown, and TXT files. Notice when I upload the same file a second time, the platform computes its SHA-256 content checksum, immediately detects the duplicate, and prevents redundant re-indexing or background worker churn."*

---

### Minute 3:30 – 5:30 | Module B & C: Advanced Hybrid RAG with Direct Citations
- **Visual:** Navigate to the **"AI Intelligence Chat"** tab.
- **Action:** Ask: *"What was the primary root cause of outage INC-89421 and what database connection pool limit was configured?"*
- **Narration:**
  > *"Here we execute a hybrid retrieval query. Our retrieval engine queries both ChromaDB dense embeddings and the BM25 sparse index, combining them using Reciprocal Rank Fusion with score thresholding to prevent hallucinations.
  > Notice the bracketed source citations `[Doc: incident_postmortem_db_pool.txt, Page: 3]`. When I click on a citation, an interactive side drawer slides open showing the exact verbatim excerpt and similarity match score."*

---

### Minute 5:30 – 7:30 | Module D: Autonomous Agent Multi-Step Workflow
- **Visual:** Toggle to **"Autonomous Agent"** mode.
- **Action:** Enter the business scenario query:
  > *"Analyze our internal technical documentation and identify the most common reasons for system failures. Provide evidence from the documents and recommend possible solutions."*
- **Narration:**
  > *"Now let's demonstrate Module D: the Autonomous Agent. Unlike a basic chatbot, our agent reasons through a LangGraph-style state machine and invokes registered functional tools.
  > Let's expand the 'Agent Execution Chain' trace:
  > In Step 1, the agent invoked `knowledge_base_search` to gather incident logs.
  > In Step 2, it piped those findings into `document_analysis` to identify recurring bottlenecks like connection pool exhaustion and retry storms.
  > In Step 3, it passed those synthesized findings into `structured_report_generator` to generate this formal enterprise incident report with actionable recommendations."*

---

### Minute 7:30 – 8:30 | Module F: Observability, Telemetry & Cost Tracking
- **Visual:** Click on the **"Observability & Metrics"** tab.
- **Narration:**
  > *"In the Observability dashboard, we provide full transparency into system operations. We track total queries, total tokens processed, estimated USD compute cost, average latency, and fallback circuit activations. The audit table logs every invocation endpoint, model, and response code."*

---

### Minute 8:30 – 10:00 | Module G: 20-Question Benchmark Suite & Wrap-Up
- **Visual:** Open `evaluation/EVALUATION_REPORT.md` and terminal showing `pytest tests/test_core.py`.
- **Narration:**
  > *"Finally, we evaluated the platform against our 20-question enterprise benchmark dataset spanning lookups, multi-document synthesis, contradictory policies, and unanswerable out-of-domain queries. As shown in our evaluation report, the platform achieved 100% Retrieval Relevance, 100% Grounding Faithfulness, and 100% Hallucination Refusal.
  > All code is covered by automated unit and live integration tests, containerized via Docker Compose, and ready for deployment. Thank you for your review, and I look forward to the live verification session!"*
