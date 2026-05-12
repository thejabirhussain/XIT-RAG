import httpx
import json
import time
from pathlib import Path
import pandas as pd

API_URL = "http://127.0.0.1:8000/query"
PROMPTS_FILE = Path("/Users/shaikmohammedjabirhussain/.gemini/antigravity/brain/9847191c-a3e0-447b-8078-c7e2ffdebb63/scratch/evaluation_prompts.json")
RESULTS_FILE = Path("/Users/shaikmohammedjabirhussain/.gemini/antigravity/brain/9847191c-a3e0-447b-8078-c7e2ffdebb63/scratch/evaluation_results.json")

def run_evaluation():
    with open(PROMPTS_FILE, "r") as f:
        prompts = json.load(f)

    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r") as f:
            results = json.load(f)
        processed_ids = {r["id"] for r in results}
    else:
        results = []
        processed_ids = set()
    
    with httpx.Client(timeout=60.0) as client:
        for p in prompts:
            if p["id"] in processed_ids:
                print(f"Skipping [{p['id']}/30]: {p['prompt']}")
                continue
                
            print(f"Running [{p['id']}/30]: {p['prompt']}")
            
            payload = {
                "query": p["prompt"],
                "model": "groq",
                "chat_history": []
            }
            
            start_time = time.perf_counter()
            try:
                response = client.post(API_URL, json=payload)
                duration = time.perf_counter() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    result = {
                        "id": p["id"],
                        "prompt": p["prompt"],
                        "category": p.get("category", ""),
                        "expected": p.get("expected_behavior", ""),
                        "answer": data.get("answer_text", ""),
                        "sql": data.get("generated_sql", "N/A"),
                        "collections": data.get("active_collection", []),
                        "chunks_count": len(data.get("sources", [])),
                        "latency": f"{duration:.2f}s",
                        "error": "None"
                    }
                else:
                    result = {
                        "id": p["id"],
                        "prompt": p["prompt"],
                        "error": f"API Error {response.status_code}: {response.text}",
                        "latency": f"{duration:.2f}s"
                    }
            except Exception as e:
                duration = time.perf_counter() - start_time
                result = {
                    "id": p["id"],
                    "prompt": p["prompt"],
                    "error": str(e),
                    "latency": f"{duration:.2f}s"
                }
            
            results.append(result)
            
            # Save incrementally
            with open(RESULTS_FILE, "w") as f:
                json.dump(results, f, indent=2)
            
            # Sleep briefly to avoid overwhelming Groq
            time.sleep(1)
    
    print(f"Evaluation complete. Saved to {RESULTS_FILE}")

if __name__ == "__main__":
    run_evaluation()
