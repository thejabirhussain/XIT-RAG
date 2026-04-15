# XIT-RAG: System Architecture & Line-By-Line Documentation 🚀

Our recent development sprints heavily optimized the XIT-RAG Query Pipeline to elevate it from a basic search API to an intelligent, conversational, and production-ready enterprise engine.

Below is the complete, explicit, line-by-line mapping of exactly who modified what in the codebase across all core developers and automated assistants.

---

## 1. File: `handlers/rag_handlers/query_handler.py`

**Maryum's Changes (Semantic Router Overhaul):**
* **Lines 118-128:** The introduction of semantic seed arrays (`IRS_INTENT_SEEDS`, `SCHEMA_INTENT_SEEDS`) and data intent boundaries.
* **Lines 130-192:** The entire `SemanticRouter` class block, which controls generating geometric centroids (`_build_centroids`) and distance calculations (`_cosine`).
* **Lines 193-207:** The `_extract_erd_entities` and `_has_data_retrieval_intent` functions, mapping english descriptions down to ERD elements.
* **Lines 212-227:** The massive refactoring of `is_schema_query`. She replaced the hardcoded regex arrays with calls to the new ERD matchers and intent functions here.
* **Line 254:** Bootstraps the new `SemanticRouter(embedding_service)` inside `__init__`.
* **Lines 283-295:** Replaces the static `is_schema` flag by utilizing `classify(query_embedding)` determining whether to target `schema` or the standard namespace collection.

**Jabir's Changes (UX Fixes & Source Objects):**
* **Line 273:** Added a robust fallback case returning: *"The query provided is unclear..."* instead of throwing silent blanks.
* **Lines 336-340:** Updated the validator string parser: `sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")`. It natively permits CTE clauses now and provides the safer fallback log here.
* **Lines 366-392:** Refactored the internal mapping block of retrieved sources so it unpacks data directly into the `Source(...)` structure rather than relying on nested dictionaries.
* **Line 420:** Final catch-all exception block changed the hardcoded database exception text to your conversational fallback: *"An unexpected error occurred... Please clarify..."*

**Recent Architecture Updates (Conversational & Debug Support):**
* **Lines 4-5:** Added `import uuid` and `import httpx` at the top of the file.
* **Lines 259:** Updated the parameters mapping of `handle_query` to explicitly accept `chat_history: Optional[list[dict[str, str]]] = None`.
* **Line 265:** Injected the UUID trace generator: `request_id = uuid.uuid4().hex[:6]`.
* **Lines 272-276:** Inserted the "Step 0" Memory Logic. If `chat_history` exists, the handler pauses and calls `self.llm.rewrite_query(chat_history, query)`.
* **Lines 277-380:** Heavily refactored the standard `logger.info` statements across the routing and generation loops to embed `[%s]` formatting, tying the logs to the `request_id`.
* **Lines 402-416:** Built two completely new exception interceptors for `httpx.RequestError` and `httpx.HTTPStatusError` that detect LLM connection delays and return polite UI messages (Network Delays/Loaded Server) rather than crashing the Python environment.

---

## 2. File: `services/rag_services/database_service.py`

**Maryum's Changes (Connection Stability):**
* **Line 39:** The single line swapping `pool_recycle=25` to `pool_recycle=1800` to prevent the recurrent *"Lost Connection to MySQL"* dropout issues over the `pymysql` pipe.

**Jabir's Changes (Optimized row maps & Security Messaging):**
* **Lines 83:** Rewrote the explicit validator exception to print *"I couldn't process this query safely..."*.
* **Lines 95-96:** Compacted the SQLAlchemy payload extraction directly into `[dict(row) for row in result.mappings().fetchmany(MAX_ROWS)]`.
* **Lines 103 & 106:** Exchanged raw SQLAlchemy/Operational stack traces crashing out of the block with two friendly fallbacks (*"I encountered an issue processing..."* & *"An unexpected issue occurred..."*).

---

## 3. File: `services/rag_services/llm_service.py`

**Maryum's Changes (Context Limits):**
* **Line 12:** Added `MAX_SCHEMA_CHUNK_CHARS = 800` globally.
* **Line 112:** Injected the splice limit on the extraction builder to enforce chunk cutoffs: `...[:MAX_SCHEMA_CHUNK_CHARS] for chunk in chunks]`.

**Jabir's Changes (LLM Instructions for DB queries):**
* **Lines 47-48:** Deeply edited `SQL_GENERATION_PROMPT` to let the Local LLM know CTEs (`WITH`...) are explicitly permitted and encouraged.
* **Line 80:** Injected the strict command block rule: *"...politely ask the user to clarify... Do not expose the technical error."*

**Recent Architecture Updates (Memory Prompt Engineering):**
* **Lines 14-38:** Designed and inserted the complex `REWRITE_QUERY_PROMPT`. This multi-shot prompt trains the LLM precisely on how to resolve ambiguous pronouns (like translating *"Are any of them active?"* into *"Are any policies active?"*).
* **Lines 82-97:** Implemented the `rewrite_query` python method. It dynamically parses the UI JSON list into a single string sequence, calls the generation LLM strictly with the `REWRITE_QUERY_PROMPT`, strips excess quotes/prefixes, and returns the mathematically perfect sentence.

---

## 4. File: `models/rag_models/requests/chat_request.py`

**Recent Architecture Updates (Schema Adjustments):**
* **Lines 6-14:** Expanded the strict Pydantic class to define `chat_history: Optional[list[dict[str, str]]] = Field(...)`. This is the exact code that allows the frontend React UI to pass dynamic lists of {"role": "user", "content": "..."} messaging arrays directly into the FastAPI backend safely.

---

## 5. File: `controllers/rag_controller.py`

**Recent Architecture Updates (API Routing Control):**
* **Lines 18-20:** Updated the central payload mapping inside `@router.post("/query")`. Extracted `request.chat_history` from the Pydantic packet and forwarded it natively into the `query_handler` orchestrator.
