import httpx
import orjson
from typing import Any, Optional

import google.generativeai as genai

OLLAMA_MODEL_ANSWER = "llama3.1:8b"   # swap to llama3.1:70b when available
GEMINI_MODEL = "gemini-pro"

COMPLIANCE_ANSWER_PROMPT = """SYSTEM:
You are a compliance management assistant for the Complyia platform.
You provide precise, data-driven answers about audit findings, risks, policies, tasks, and frameworks.
Always flag compliance risks clearly. Never invent data or regulatory facts.

CONTEXT:
{context}

USER QUESTION:
{query}

INSTRUCTIONS:
- Use ONLY the provided context.
- Respond in GitHub-Flavored Markdown (GFM).
- Begin with: ### {query}
- If context contains database rows: present key data in a markdown table.
- If context contains document excerpts: use bullet points with specific citations.
- Bold critical compliance terms: **critical**, **open**, **overdue**, **high risk**, **non-conformity**.
- End with a short **Compliance Note** if any urgent items (critical findings, overdue policies, high risk scores) are present.
- If the data is insufficient, respond: "The compliance database does not contain sufficient data to answer this query for org_id {org_id}."
- DO NOT invent risk scores, audit outcomes, or regulatory requirements."""


class LLM2Service:
    def __init__(self, ollama_host: str, gemini_api_key: Optional[str] = None):
        self.ollama_client = httpx.Client(base_url=ollama_host, timeout=120.0)
        self.gemini_api_key = gemini_api_key
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel(GEMINI_MODEL)

    def generate_answer(
        self,
        query: str,
        context: str,
        org_id: int,
        model: str = "gemini",
        max_tokens: int = 800,
    ) -> str:
        prompt = COMPLIANCE_ANSWER_PROMPT.format(
            context=context,
            query=query,
            org_id=org_id,
        )
        if model == "gemini" and self.gemini_api_key:
            return self._generate_gemini(prompt, max_tokens=max_tokens)
        return self._generate_ollama(prompt, max_tokens=max_tokens)

    def _generate_ollama(self, prompt: str, max_tokens: int = 800) -> str:
        response = self.ollama_client.post(
            "/api/generate",
            json={
                "model": OLLAMA_MODEL_ANSWER,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": max_tokens},
            },
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()

    def _generate_gemini(self, prompt: str, max_tokens: int = 800) -> str:
        try:
            config = genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=max_tokens,
            )
            response = self.gemini_model.generate_content(prompt, generation_config=config)
            return response.text
        except Exception as e:
            return f"Error generating response from Gemini: {str(e)}"

    @staticmethod
    def format_sql_context(sql: str, rows: list[dict[str, Any]]) -> str:
        """Converts SQL query result into a readable context block."""
        if not rows:
            return f"[SQL RESULT]\nQuery: {sql}\nResult: No rows returned."
        headers = list(rows[0].keys())
        header_line = " | ".join(headers)
        separator = " | ".join(["---"] * len(headers))
        row_lines = [
            " | ".join(str(row.get(h, "")) for h in headers)
            for row in rows[:50]  # cap at 50 rows for context window
        ]
        table = "\n".join([header_line, separator] + row_lines)
        return f"[DATABASE RESULT — {len(rows)} rows]\nGenerated SQL: {sql}\n\n{table}"

    @staticmethod
    def format_vector_context(chunks: list[dict[str, Any]]) -> str:
        """Converts vector chunks into a readable context block."""
        lines = []
        for i, chunk in enumerate(chunks, 1):
            obj = {
                "source": chunk.get("url", "compliance-doc"),
                "title": chunk.get("title", ""),
                "section": chunk.get("section_heading", ""),
                "excerpt": chunk.get("text", "")[:400],
            }
            lines.append(f"[DOC {i}] {orjson.dumps(obj).decode('utf-8')}")
        return "[KNOWLEDGE BASE RESULTS]\n" + "\n".join(lines)
