# XIT-RAG × Qwen QwQ-32B (Groq) — Database Query Evaluation Report

> **Generated:** 2026-05-01 22:29:31  
> **Model:** `qwen-qwq-32b` via Groq API  
> **Integration:** `model="groq"` in POST /query  
> **Total Queries:** 15 | **Successful:** 7 | **Errors:** 8 | **Avg Latency:** 7968ms

---

## Summary Table

| # | Category | Query (truncated) | Confidence | SQL Generated | Rows | Latency |
|---|----------|-------------------|------------|---------------|------|---------|
| 1 | Simple — Single Table | How many policies are there in total? | 🔴 low | — | 0 | 13091.6ms |
| 2 | Simple — Single Table | List all published policies. | 🔴 low | — | 0 | 3198.5ms |
| 3 | Simple — Single Table | How many users exist in the system? | 🔴 low | — | 0 | 21948.1ms |
| 4 | Simple — Single Table | Show me all organizations. | 🔴 low | ✅ | 0 | 16261.1ms |
| 5 | Simple — Single Table | What are all the compliance frameworks in the system? | 🟢 high | ✅ | 0 | 21187.8ms |
| 6 | Aggregation | How many risks are open vs mitigated? Give me the count for ... | ❌ error | — | ERR | 11.9ms |
| 7 | Aggregation | What is the distribution of policies by status (draft, publi... | ❌ error | — | ERR | 8.5ms |
| 8 | Aggregation | How many controls are there per framework? | ❌ error | — | ERR | 8.7ms |
| 9 | Multi-Table Join | Show me all findings along with their associated audit detai... | ❌ error | — | ERR | 10.2ms |
| 10 | Multi-Table Join | Which users are assigned to which organizations? | ❌ error | — | ERR | 17.4ms |
| 11 | Multi-Table Join | List all risks along with their associated policies and risk... | ❌ error | — | ERR | 7.8ms |
| 12 | Conditional Filtering | Show me all high-risk items — where the risk score is above ... | ❌ error | — | ERR | 7.0ms |
| 13 | Conditional Filtering | Which audits have a status of completed or closed? | ❌ error | — | ERR | 7.3ms |
| 14 | Complex — Multi-Hop | For each organization, how many open risks do they have? Sho... | 🔴 low | ✅ | 0 | 17225.2ms |
| 15 | Complex — Multi-Hop | Which frameworks have the most controls mapped to them, and ... | 🔴 low | ✅ | 0 | 26531.4ms |

---

## Detailed Results

### 📂 Simple — Single Table

#### Query 1: How many policies are there in total?

- **Confidence:** low
- **Latency:** 13091.6ms
- **Records returned:** N/A

**Model Answer (Qwen QwQ-32B):**

It seems I encountered an issue retrieving the total policy count. Could you please clarify or rephrase your request?

---

#### Query 2: List all published policies.

- **Confidence:** low
- **Latency:** 3198.5ms
- **Records returned:** N/A

**Model Answer (Qwen QwQ-32B):**

I encountered an issue retrieving the requested policy data. Could you clarify or rephrase your query about published policies? The system requires additional details to safely process this request.

---

#### Query 3: How many users exist in the system?

- **Confidence:** low
- **Latency:** 21948.1ms
- **Records returned:** N/A

**Model Answer (Qwen QwQ-32B):**

I encountered an issue retrieving the total user count. Could you clarify or rephrase your request? The system may require additional context (e.g., organization scope) or permissions to access this information.

---

#### Query 4: Show me all organizations.

- **Confidence:** low
- **Latency:** 16261.1ms
- **Records returned:** N/A

**Generated SQL:**
```sql
SELECT * FROM organizations LIMIT 50;
```

**Model Answer (Qwen QwQ-32B):**

It seems I encountered an issue retrieving the list of organizations. Could you please **clarify or rephrase** your request? For example, you might specify a particular industry, country, or another filter to narrow the scope. Let me know how you'd like to proceed!

---

#### Query 5: What are all the compliance frameworks in the system?

- **Confidence:** high
- **Latency:** 21187.8ms
- **Records returned:** N/A

**Generated SQL:**
```sql
SELECT * FROM compliance_platform_v3.frameworks LIMIT 50;
```

**Model Answer (Qwen QwQ-32B):**

I encountered an issue retrieving the list of compliance frameworks. Could you please **clarify or rephrase** your request to ensure I accurately understand what you're seeking? For example, specify if you need framework names, versions, or additional metadata.

---

### 📂 Aggregation

#### Query 6: How many risks are open vs mitigated? Give me the count for each status.

- **Confidence:** error
- **Latency:** 11.9ms
- **Records returned:** N/A

> ❌ **Error:** [Errno 61] Connection refused

#### Query 7: What is the distribution of policies by status (draft, published, archived)?

- **Confidence:** error
- **Latency:** 8.5ms
- **Records returned:** N/A

> ❌ **Error:** [Errno 61] Connection refused

#### Query 8: How many controls are there per framework?

- **Confidence:** error
- **Latency:** 8.7ms
- **Records returned:** N/A

> ❌ **Error:** [Errno 61] Connection refused

### 📂 Multi-Table Join

#### Query 9: Show me all findings along with their associated audit details.

- **Confidence:** error
- **Latency:** 10.2ms
- **Records returned:** N/A

> ❌ **Error:** [Errno 61] Connection refused

#### Query 10: Which users are assigned to which organizations?

- **Confidence:** error
- **Latency:** 17.4ms
- **Records returned:** N/A

> ❌ **Error:** [Errno 61] Connection refused

#### Query 11: List all risks along with their associated policies and risk scores.

- **Confidence:** error
- **Latency:** 7.8ms
- **Records returned:** N/A

> ❌ **Error:** [Errno 61] Connection refused

### 📂 Conditional Filtering

#### Query 12: Show me all high-risk items — where the risk score is above 7.

- **Confidence:** error
- **Latency:** 7.0ms
- **Records returned:** N/A

> ❌ **Error:** [Errno 61] Connection refused

#### Query 13: Which audits have a status of completed or closed?

- **Confidence:** error
- **Latency:** 7.3ms
- **Records returned:** N/A

> ❌ **Error:** [Errno 61] Connection refused

### 📂 Complex — Multi-Hop

#### Query 14: For each organization, how many open risks do they have? Show org name and count, ordered by most risks first.

- **Confidence:** low
- **Latency:** 17225.2ms
- **Records returned:** N/A

**Generated SQL:**
```sql
SELECT o.name, COUNT(*) AS open_risks FROM risks r JOIN organizations o ON r.org_id = o.org_id WHERE r.status = 'open' GROUP BY o.name ORDER BY open_risks DESC LIMIT 50;
```

**Model Answer (Qwen QwQ-32B):**

I encountered an issue retrieving the requested risk counts. Could you clarify or rephrase your query?

---

#### Query 15: Which frameworks have the most controls mapped to them, and how many findings are associated with those controls?

- **Confidence:** low
- **Latency:** 26531.4ms
- **Records returned:** N/A

**Generated SQL:**
```sql
WITH control_counts AS (
    SELECT c.framework_id, COUNT(c.control_id) AS control_count
    FROM controls c
    GROUP BY c.framework_id
),
finding_counts AS (
    SELECT af.control_id, COUNT(af.finding_id) AS finding_count
    FROM audit_findings af
    GROUP BY af.control_id
),
framework_findings AS (
    SELECT c.framework_id, SUM(fc.finding_count) AS total_findings
    FROM controls c
    LEFT JOIN finding_counts fc ON c.control_id = fc.control_id
    GROUP BY c.framework_id
)
SELECT 
    f.name AS framework_name, 
    cc.control_count, 
    COALESCE(ff.total_findings, 0) AS total_findings
FROM frameworks f
JOIN control_counts cc ON f.framework_id = cc.framework_id
LEFT JOIN framework_findings ff ON f.framework_id = ff.framework_id
ORDER BY cc.control_count DESC
LIMIT 50;
```

**Model Answer (Qwen QwQ-32B):**

I encountered an issue processing your request to analyze frameworks by control count and associated findings. Could you clarify or rephrase your query? For example:
- Are you looking for top 5 frameworks by control count?
- Should findings be counted at the control level or framework level?
- Do you need findings filtered by status (open/closed)?

The system requires precise scoping for multi-tenant data, so specifying organizational context may also help.

---

## Performance Analysis

| Category | Count | Avg Latency | Success Rate |
|----------|-------|-------------|--------------|
| Simple — Single Table | 5 | 15137ms | 5/5 |
| Aggregation | 3 | 10ms | 0/3 |
| Multi-Table Join | 3 | 12ms | 0/3 |
| Conditional Filtering | 2 | 7ms | 0/2 |
| Complex — Multi-Hop | 2 | 21878ms | 2/2 |

---

## Integration Notes

- **How the model is invoked:** `POST /query` with `model: "groq"` in the request body.
- **LLM routing path:** `LLMService.generate()` → `_generate_groq()` → Groq SDK `chat.completions.create()`
- **Model used:** `qwen-qwq-32b` (Qwen's 32B reasoning model, hosted on Groq for ultra-fast inference)
- **Existing pipeline unchanged:** Embedding, vector retrieval, reranking, SQL generation and execution all flow identically to the Ollama/Gemini paths. Only the final LLM generation call is different.
- **Caching:** Response cache is active for temperature=0.0 calls (5-minute TTL).
- **Cost tracking:** Groq token usage is recorded in the shared `_cost_tracker` dict, visible at `GET /cost-stats`.
