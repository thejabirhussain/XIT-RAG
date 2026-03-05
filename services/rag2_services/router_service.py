import json
import httpx
from typing import Tuple

ROUTER_MODEL = "llama3.1:8b"

# Compliance-domain routing prompt — replaces the generic "sales/orders" vocabulary
# from the architecture doc with actual compliance domain vocabulary
ROUTER_SYSTEM_PROMPT = """You are a compliance query classifier. Respond ONLY with valid JSON.
Format: {"route": "structured" | "knowledge" | "hybrid", "confidence": 0.0-1.0}

"structured" -> requires looking up SPECIFIC DATA from the compliance database.
Triggers: audit status, open findings, overdue policies, risk scores, task assignments,
          user roles, evidence uploads, which org has X, how many findings, list all tasks,
          show risks above score N, policies owned by person, auditor name.

"knowledge"  -> conceptual or regulatory question answerable from compliance framework documents.
Triggers: what does ISO 27001 require, how does SOC 2 work, what is HIPAA, explain a control,
          compliance best practices, what is a risk score, framework comparison, define audit finding.

"hybrid"     -> needs BOTH database data AND regulatory/framework knowledge.
Triggers: how do our risks compare to ISO 27001 benchmarks, are we above industry standard,
          does our policy coverage meet SOC 2, gap analysis against a framework."""

ROUTER_USER_TEMPLATE = 'Query: "{query}"'


class RouterService:
    def __init__(self, ollama_host: str):
        self.client = httpx.Client(base_url=ollama_host, timeout=30.0)

    def classify(self, query: str) -> Tuple[str, float]:
        """
        Returns (route, confidence).
        route: "structured" | "knowledge" | "hybrid"
        Falls back to "knowledge" on any parse error.
        """
        prompt = f"{ROUTER_SYSTEM_PROMPT}\n\nUSER:\n{ROUTER_USER_TEMPLATE.format(query=query)}"
        try:
            response = self.client.post(
                "/api/generate",
                json={
                    "model": ROUTER_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.0, "num_predict": 60},
                },
            )
            response.raise_for_status()
            raw = response.json().get("response", "{}")
            parsed = json.loads(raw)
            route = parsed.get("route", "knowledge")
            confidence = float(parsed.get("confidence", 0.5))

            # Validate route value
            if route not in ("structured", "knowledge", "hybrid"):
                route = "knowledge"
                confidence = 0.5

            return route, confidence

        except Exception:
            # Safe fallback — never drop the query
            return "knowledge", 0.5
