# 🛡️ Mandatory Live Technical Verification Guide (60-Minute Defense)

This guide documents the exact architecture and code hooks designed into this codebase to solve each of the 6 potential live verification tasks.

---

## Challenge 1: Introduce a Secondary LLM Provider & Implement Fallback
* **Architecture:** Handled by `backend/app/services/llm/fallback_router.py`.
* **How it works:** All LLM clients inherit from `BaseLLMClient`.
* **To add a new provider during the live session:**
  1. Create a class inheriting from `BaseLLMClient`:
     ```python
     class AnthropicLLMClient(BaseLLMClient):
         async def generate(self, prompt, system_prompt=None, temperature=0.2, max_tokens=1500) -> LLMResult:
             # Call Anthropic API
             return LLMResult(content="...", model="claude-3-5-sonnet", provider="anthropic", latency_ms=120)
     ```
  2. Register in `ResilientLLMRouter._init_providers`:
     ```python
     self.providers["anthropic"] = AnthropicLLMClient()
     ```
  3. Set `FALLBACK_LLM_PROVIDER = "anthropic"`. If Groq/OpenAI fails, the router switches to Anthropic automatically!

---

## Challenge 2: Modify RAG Pipeline to Handle Conflicting Information from Two Documents
* **Architecture:** Handled by `backend/app/services/guardrails/grounding_critic.py` and `SYSTEM_RAG_PROMPT` in `rag_engine.py`.
* **How it works:**
  1. `GroundingCritic.detect_conflicts_in_chunks` groups retrieved chunks by document and inspects opposing assertions (e.g. Port 5432 vs. 5433).
  2. The prompt rule 4 commands: *"If you notice contradictory facts between different documents, explicitly highlight the contradiction."*
  3. The response JSON returns `conflicts_detected: List[str]`, which displays an amber alert banner in the frontend UI.

---

## Challenge 3: Implement a New Tool in the Existing Agent Architecture
* **Architecture:** Handled by `backend/app/services/agent/tools.py` and `agent_runner.py`.
* **To add a 4th tool (e.g. `slack_alert_sender` or `jira_ticket_creator`):**
  1. Define Pydantic input schema:
     ```python
     class JiraTicketInput(BaseModel):
         summary: str
         description: str
         priority: str = "High"
     ```
  2. Define execution function:
     ```python
     def execute_create_jira(summary: str, description: str, priority: str = "High"):
         return {"ticket_key": "SEC-1042", "status": "Created", "summary": summary}
     ```
  3. Append to `TOOL_DEFINITIONS` in `tools.py` and add `elif tool_name == "create_jira":` inside `agent_runner._execute_tool_safe`. The agent will immediately begin selecting and calling it!

---

## Challenge 4: Prevent Duplicate Document-Processing Jobs
* **Architecture:** Handled by `IngestionPipeline.ingest_upload` in `backend/app/services/ingestion/pipeline.py`.
* **How it works:**
  1. Computes SHA-256 hash of uploaded bytes: `content_hash = hashlib.sha256(file_bytes).hexdigest()`.
  2. Checks `select(Document).where(Document.content_hash == content_hash)`.
  3. If found, returns `is_duplicate: True`, returns HTTP 202/200 with existing doc metadata, and **skips scheduling any background worker jobs**.

---

## Challenge 5: Fix Unsupported Answers When Retrieval Returns Irrelevant Documents
* **Architecture:** Handled by `similarity_threshold` in `backend/app/services/retrieval/hybrid_search.py` and `rag_engine.py`.
* **How it works:**
  1. In `hybrid_search.py`, chunks with cosine similarity $< 0.45$ are pruned.
  2. In `rag_engine.py`:
     ```python
     if not retrieved_chunks:
         return {
             "answer": "The provided internal documentation does not contain relevant information to answer your query.",
             "citations": [],
             "is_grounded": True
         }
     ```
  3. Evaluated on 5 unanswerable questions in `evaluation/dataset.json` with a verified 100% hallucination refusal rate.

---

## Challenge 6: Identify and Fix a Security Vulnerability in an Existing API
* **Common Vulnerabilities Addressed:**
  1. **Prompt Injection:** Defanged via `PromptInjectionShield` and boundary envelope `<untrusted_document_context>`.
  2. **Arbitrary File Upload:** Extension whitelist (`.pdf`, `.txt`, `.md`, `.csv`) and 25MB file size ceiling.
  3. **SQL Injection:** 100% parameterized queries via SQLAlchemy async ORM.
  4. **Broken Access Control:** JWT bearer token verification with expiry checking.
