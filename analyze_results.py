import json
from pathlib import Path
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
model_id = "qwen/qwen3-32b"

RESULTS_FILE = Path("/Users/shaikmohammedjabirhussain/.gemini/antigravity/brain/9847191c-a3e0-447b-8078-c7e2ffdebb63/scratch/evaluation_results.json")
ANALYSIS_FILE = Path("/Users/shaikmohammedjabirhussain/.gemini/antigravity/brain/9847191c-a3e0-447b-8078-c7e2ffdebb63/scratch/evaluation_analysis.json")

def analyze_results():
    if not RESULTS_FILE.exists():
        print("Results file not found.")
        return

    with open(RESULTS_FILE, "r") as f:
        results = json.load(f)

    if ANALYSIS_FILE.exists():
        with open(ANALYSIS_FILE, "r") as f:
            try:
                analysis = json.load(f)
            except:
                analysis = []
        processed_ids = {r["id"] for r in analysis if r.get("accuracy_status") != "Error"}
    else:
        analysis = []
        processed_ids = set()
    
    for r in results:
        if r["id"] in processed_ids:
            print(f"Skipping [{r['id']}/30]: {r['prompt']}")
            continue
            
        print(f"Analyzing [{r['id']}/30]: {r['prompt']}")
        
        prompt_for_eval = f"""
        You are an expert QA evaluator for a RAG-based SQL agent.
        Analyze the following system output for the given prompt.
        
        PROMPT: {r['prompt']}
        EXPECTED: {r['expected']}
        GENERATED SQL: {r['sql']}
        SYSTEM ANSWER: {r['answer']}
        ERROR: {r['error']}
        
        Provide a JSON analysis with these fields:
        - accuracy_status: (Correct / Partially Correct / Wrong)
        - hallucination_check: (Pass / Fail - explain if fail)
        - sql_accuracy: (High / Medium / Low / Failed)
        - retrieval_accuracy: (High / Medium / Low / None)
        - guardrail_validation: (Pass / Fail / N/A)
        - final_remarks: (Short summary)
        
        ONLY return the raw JSON.
        """
        
        try:
            resp = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt_for_eval}],
                response_format={"type": "json_object"}
            )
            text = resp.choices[0].message.content
            eval_data = json.loads(text)
            
            analysis.append({
                "id": r["id"],
                "prompt": r["prompt"],
                "expected": r["expected"],
                "actual_summary": r["answer"][:200] + "..." if len(r["answer"]) > 200 else r["answer"],
                **eval_data
            })
            
            # Save incrementally
            with open(ANALYSIS_FILE, "w") as f:
                json.dump(analysis, f, indent=2)
        except Exception as e:
            print(f"Error analyzing {r['id']}: {e}")
            analysis.append({
                "id": r["id"],
                "prompt": r["prompt"],
                "accuracy_status": "Error",
                "final_remarks": str(e)
            })

    with open(ANALYSIS_FILE, "w") as f:
        json.dump(analysis, f, indent=2)
    
    print(f"Analysis complete. Saved to {ANALYSIS_FILE}")

if __name__ == "__main__":
    analyze_results()
