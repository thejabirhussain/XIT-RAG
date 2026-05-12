import json
import pandas as pd
from pathlib import Path

RESULTS_FILE = Path("/Users/shaikmohammedjabirhussain/.gemini/antigravity/brain/9847191c-a3e0-447b-8078-c7e2ffdebb63/scratch/evaluation_results.json")
ANALYSIS_FILE = Path("/Users/shaikmohammedjabirhussain/.gemini/antigravity/brain/9847191c-a3e0-447b-8078-c7e2ffdebb63/scratch/evaluation_analysis.json")
OUTPUT_EXCEL = Path("/Users/shaikmohammedjabirhussain/Desktop/XIT-RAG/Qwen_24B_Evaluation_Results.xlsx")

def generate_excel():
    if not RESULTS_FILE.exists() or not ANALYSIS_FILE.exists():
        print("Required JSON files missing.")
        return

    with open(RESULTS_FILE, "r") as f:
        results = json.load(f)
    with open(ANALYSIS_FILE, "r") as f:
        analysis = json.load(f)

    # Sheet 1: Testing
    testing_data = []
    for r in results:
        # Match analysis to get observations if any
        eval_item = next((a for a in analysis if a["id"] == r["id"]), {})
        
        testing_data.append({
            "Query ID": r["id"],
            "Prompt/Query": r["prompt"],
            "Retrieved Collections": r["collections"] if r["collections"] else "None",
            "Retrieved Chunks": r["chunks_count"],
            "SQL Generated": r["sql"],
            "Final Output": r["answer"],
            "Response Time": r["latency"],
            "Observations": eval_item.get("final_remarks", ""),
            "Errors": r["error"] if r["error"] != "None" else ""
        })
    
    # Sheet 2: Analysis
    analysis_data = []
    for a in analysis:
        analysis_data.append({
            "Query ID": a["id"],
            "Prompt": a["prompt"],
            "Expected Behavior": a.get("expected", ""),
            "Actual Output Summary": a.get("actual_summary", ""),
            "Accuracy Status": a.get("accuracy_status", ""),
            "Hallucination Check": a.get("hallucination_check", ""),
            "SQL Accuracy": a.get("sql_accuracy", ""),
            "Retrieval Accuracy": a.get("retrieval_accuracy", ""),
            "Guardrail Validation": a.get("guardrail_validation", ""),
            "Follow-up Handling": "N/A",
            "Final Remarks": a.get("final_remarks", "")
        })

    with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
        pd.DataFrame(testing_data).to_excel(writer, sheet_name="Qwen 24B Testing", index=False)
        pd.DataFrame(analysis_data).to_excel(writer, sheet_name="Qwen 24B Analysis", index=False)

    print(f"Excel file generated at {OUTPUT_EXCEL}")

if __name__ == "__main__":
    generate_excel()
