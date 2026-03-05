import re
import httpx
from typing import Optional

# ---------------------------------------------------------------------------
# Compact MS SQL schema — matches the Complyia compliance_platform schema
# but with MS SQL syntax (IDENTITY, NVARCHAR, GETDATE, computed column).
# org_id is present on: organizations, users, policies, audits, risks, tasks
# ---------------------------------------------------------------------------
COMPLIANCE_SCHEMA_MSSQL = """
-- MS SQL Server | Complyia Compliance Platform

organizations (
  org_id        INT IDENTITY(1,1) PRIMARY KEY,
  name          NVARCHAR(150) NOT NULL,
  industry      NVARCHAR(100),
  country       NVARCHAR(100),
  created_at    DATETIME DEFAULT GETDATE()
)

users (
  user_id       INT IDENTITY(1,1) PRIMARY KEY,
  org_id        INT NOT NULL REFERENCES organizations(org_id),
  full_name     NVARCHAR(150) NOT NULL,
  email         NVARCHAR(150) NOT NULL UNIQUE,
  role          NVARCHAR(50),   -- admin | auditor | analyst | viewer
  created_at    DATETIME DEFAULT GETDATE()
)

frameworks (
  framework_id  INT IDENTITY(1,1) PRIMARY KEY,
  name          NVARCHAR(100) NOT NULL,  -- 'ISO 27001' | 'SOC 2' | 'HIPAA'
  version       NVARCHAR(20),
  description   NVARCHAR(MAX)
)

controls (
  control_id    INT IDENTITY(1,1) PRIMARY KEY,
  framework_id  INT NOT NULL REFERENCES frameworks(framework_id),
  control_code  NVARCHAR(30) NOT NULL,  -- e.g. 'ISO-A.5.1', 'SOC-CC6.1'
  title         NVARCHAR(200) NOT NULL,
  description   NVARCHAR(MAX),
  category      NVARCHAR(100)  -- Governance | Asset Management | Access Control | Monitoring | Data Protection
)

policies (
  policy_id     INT IDENTITY(1,1) PRIMARY KEY,
  org_id        INT NOT NULL REFERENCES organizations(org_id),
  control_id    INT NOT NULL REFERENCES controls(control_id),
  title         NVARCHAR(200) NOT NULL,
  status        NVARCHAR(30),  -- draft | active | retired
  owner_id      INT REFERENCES users(user_id),
  review_date   DATE
)

audits (
  audit_id      INT IDENTITY(1,1) PRIMARY KEY,
  org_id        INT NOT NULL REFERENCES organizations(org_id),
  framework_id  INT NOT NULL REFERENCES frameworks(framework_id),
  auditor_id    INT REFERENCES users(user_id),
  audit_name    NVARCHAR(200),
  start_date    DATE,
  end_date      DATE,
  status        NVARCHAR(30)   -- planned | in_progress | completed | cancelled
)

audit_findings (
  finding_id    INT IDENTITY(1,1) PRIMARY KEY,
  audit_id      INT NOT NULL REFERENCES audits(audit_id),
  control_id    INT NOT NULL REFERENCES controls(control_id),
  severity      NVARCHAR(20),  -- low | medium | high | critical
  title         NVARCHAR(200),
  description   NVARCHAR(MAX),
  status        NVARCHAR(30)   -- open | in_remediation | closed
)
-- Note: audit_findings has no direct org_id — always JOIN audits to scope by org_id

risks (
  risk_id       INT IDENTITY(1,1) PRIMARY KEY,
  org_id        INT NOT NULL REFERENCES organizations(org_id),
  control_id    INT REFERENCES controls(control_id),
  title         NVARCHAR(200),
  likelihood    INT,           -- 1 to 5
  impact        INT,           -- 1 to 5
  risk_score    AS (likelihood * impact) PERSISTED,  -- COMPUTED, READ-ONLY
  owner_id      INT REFERENCES users(user_id),
  status        NVARCHAR(30)   -- open | mitigated | accepted | closed
)

tasks (
  task_id       INT IDENTITY(1,1) PRIMARY KEY,
  org_id        INT NOT NULL REFERENCES organizations(org_id),
  assigned_to   INT REFERENCES users(user_id),
  finding_id    INT REFERENCES audit_findings(finding_id),
  risk_id       INT REFERENCES risks(risk_id),
  title         NVARCHAR(200),
  due_date      DATE,
  priority      NVARCHAR(20),  -- low | medium | high
  status        NVARCHAR(30)   -- todo | in_progress | done
)

evidence (
  evidence_id   INT IDENTITY(1,1) PRIMARY KEY,
  task_id       INT REFERENCES tasks(task_id),
  audit_id      INT REFERENCES audits(audit_id),
  uploaded_by   INT REFERENCES users(user_id),
  file_name     NVARCHAR(255),
  file_type     NVARCHAR(50),
  description   NVARCHAR(MAX),
  uploaded_at   DATETIME DEFAULT GETDATE()
)
"""

TEXT2SQL_PROMPT = """You are an expert MS SQL query generator for the Complyia compliance platform.

DATABASE SCHEMA:
{schema}

CRITICAL RULES — follow exactly, no exceptions:
1. Generate ONLY a SELECT statement. Never INSERT, UPDATE, DELETE, DROP, ALTER, EXEC, or MERGE.
2. ALWAYS scope the query to the tenant: include WHERE org_id = {org_id} directly, or JOIN to a
   table that has org_id = {org_id}. Every result must belong to this organization.
3. NEVER include risk_score in an INSERT or UPDATE — it is a PERSISTED computed column.
4. Use MS SQL syntax: TOP N (not LIMIT), GETDATE() (not NOW()), NVARCHAR (not TEXT/VARCHAR for schema matches).
5. For date comparisons use: CAST(GETDATE() AS DATE) for today's date.
6. audit_findings has no org_id — always JOIN audits ON af.audit_id = a.audit_id WHERE a.org_id = {org_id}.
7. Respond with ONLY the raw SQL query. No explanation, no markdown fences, no backticks.

QUESTION:
{query}

SQL:"""


class Text2SQLService:
    def __init__(self, ollama_host: str, model: str = "llama3.1:8b"):
        """
        For POC: uses llama3.1:8b (already running on your Ollama).
        Production swap: change model to "arctic-text2sql-r1:7b" when available on Ollama,
        or override via TEXT2SQL_MODEL env var.
        """
        self.client = httpx.Client(base_url=ollama_host, timeout=60.0)
        self.model = model

    def generate_sql(self, query: str, org_id: int) -> str:
        prompt = TEXT2SQL_PROMPT.format(
            schema=schema_context,
            org_id=org_id,
            query=query,
        )
        response = self.client.post(
            "/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 400},
            },
        )
        response.raise_for_status()
        raw_sql = response.json().get("response", "").strip()

        # Strip any accidental markdown fences the model may produce
        raw_sql = self._clean_sql(raw_sql)
        return raw_sql

    @staticmethod
    def _clean_sql(text: str) -> str:
        # Remove ```sql ... ``` or ``` ... ``` fences
        text = re.sub(r"```(?:sql)?", "", text, flags=re.IGNORECASE)
        text = text.replace("```", "").strip()
        # Take only the first statement if model returned multiple
        if ";" in text:
            text = text.split(";")[0].strip() + ";"
        return text
