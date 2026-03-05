import re
import httpx

COMPLIANCE_SCHEMA_MYSQL = """
-- MySQL | Complyia Compliance Platform (freedb_RAGPOC2)

organizations (
  org_id      INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(150) NOT NULL,
  industry    VARCHAR(100),
  country     VARCHAR(100),
  created_at  DATETIME DEFAULT NOW()
)

users (
  user_id     INT AUTO_INCREMENT PRIMARY KEY,
  org_id      INT NOT NULL,
  full_name   VARCHAR(150) NOT NULL,
  email       VARCHAR(150) NOT NULL UNIQUE,
  role        VARCHAR(50),
  created_at  DATETIME DEFAULT NOW()
)

frameworks (
  framework_id  INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,
  version       VARCHAR(20),
  description   TEXT
)

controls (
  control_id    INT AUTO_INCREMENT PRIMARY KEY,
  framework_id  INT NOT NULL,
  control_code  VARCHAR(30) NOT NULL,
  title         VARCHAR(200) NOT NULL,
  description   TEXT,
  category      VARCHAR(100)
)

policies (
  policy_id   INT AUTO_INCREMENT PRIMARY KEY,
  org_id      INT NOT NULL,
  control_id  INT NOT NULL,
  title       VARCHAR(200) NOT NULL,
  status      VARCHAR(30),
  owner_id    INT,
  review_date DATE
)

audits (
  audit_id      INT AUTO_INCREMENT PRIMARY KEY,
  org_id        INT NOT NULL,
  framework_id  INT NOT NULL,
  auditor_id    INT,
  audit_name    VARCHAR(200),
  start_date    DATE,
  end_date      DATE,
  status        VARCHAR(30)
)

audit_findings (
  finding_id  INT AUTO_INCREMENT PRIMARY KEY,
  audit_id    INT NOT NULL,
  control_id  INT NOT NULL,
  severity    VARCHAR(20),
  title       VARCHAR(200),
  description TEXT,
  status      VARCHAR(30)
)

risks (
  risk_id     INT AUTO_INCREMENT PRIMARY KEY,
  org_id      INT NOT NULL,
  control_id  INT,
  title       VARCHAR(200),
  likelihood  INT,
  impact      INT,
  risk_score  INT,
  owner_id    INT,
  status      VARCHAR(30)
)

tasks (
  task_id     INT AUTO_INCREMENT PRIMARY KEY,
  org_id      INT NOT NULL,
  assigned_to INT,
  finding_id  INT,
  risk_id     INT,
  title       VARCHAR(200),
  due_date    DATE,
  priority    VARCHAR(20),
  status      VARCHAR(30)
)

evidence (
  evidence_id INT AUTO_INCREMENT PRIMARY KEY,
  task_id     INT,
  audit_id    INT,
  uploaded_by INT,
  file_name   VARCHAR(255),
  file_type   VARCHAR(50),
  description TEXT,
  uploaded_at DATETIME DEFAULT NOW()
)
"""

TEXT2SQL_PROMPT = """You are an expert MySQL query generator for the Complyia compliance platform.

DATABASE SCHEMA:
{schema}

CRITICAL RULES — follow exactly:
1. Generate ONLY a SELECT statement. Never INSERT, UPDATE, DELETE, DROP, ALTER, EXEC, or MERGE.
2. ALWAYS scope to the tenant: include WHERE org_id = {org_id}, or JOIN to a table with org_id = {org_id}.
3. NEVER write to risk_score — it is a read-only computed column.
4. Use MySQL syntax: LIMIT N (not TOP N), NOW() / CURDATE() (not GETDATE()), VARCHAR (not NVARCHAR).
5. For today's date use: CURDATE()
6. audit_findings has no org_id — always JOIN audits ON af.audit_id = a.audit_id WHERE a.org_id = {org_id}.
7. Respond with ONLY the raw SQL. No explanation, no markdown fences, no backticks.

QUESTION:
{query}

SQL:"""


class Text2SQLService:
    def __init__(self, ollama_host: str, model: str = "llama3.1:8b"):
        self.client = httpx.Client(base_url=ollama_host, timeout=200.0)
        self.model = model

    def generate_sql(self, query: str, org_id: int, schema_context: str) -> str:
        schema = schema_context.strip()

        system_msg = f"""You are a MySQL query generator. You output ONLY raw SQL. 
    No explanations. No reasoning. No markdown. No backticks. No commentary.
    Your entire response must be a single valid SELECT statement and nothing else.

    DATABASE SCHEMA:
    {schema}

    RULES:
    1. Output ONLY a SELECT statement. Nothing before it. Nothing after it.
    2. Always include WHERE org_id = {org_id} or JOIN to a table where org_id = {org_id}.
    3. audit_findings has no org_id — JOIN audits ON af.audit_id = a.audit_id WHERE a.org_id = {org_id}.
    4. Use MySQL syntax: LIMIT not TOP, CURDATE() not GETDATE().
    5. Never write to risk_score."""

        user_msg = f"Question: {query}\n\nSQL:"

        response = self.client.post(
            "/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user",   "content": user_msg},
                ],
                "options": {"temperature": 0.0, "num_predict": 200},
            },
        )
        response.raise_for_status()
        raw_sql = response.json()["message"]["content"].strip()
       # logger.info(f"[Text2SQL] Raw model output: {raw_sql[:300]}")
        return self._clean_sql(raw_sql)

    @staticmethod
    def _clean_sql(text: str) -> str:

        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r".*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Remove markdown fences
        text = re.sub(r"```(?:sql)?", "", text, flags=re.IGNORECASE)
        text = text.replace("```", "").strip()

       # If model still added reasoning before the SELECT, extract from SELECT onward
        select_match = re.search(r"\bSELECT\b", text, re.IGNORECASE| re.MULTILINE)
        if select_match:
            text = text[select_match.start():]

        # Take only first statement
        if ";" in text:
            text = text.split(";")[0].strip() + ";"

        return text.strip()

