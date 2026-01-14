import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def test_model(model_name, query):
    print(f"\n--- Testing {model_name} ---")
    payload = {
        "query": query,
        "model": model_name
    }
    try:
        response = requests.post(f"{BASE_URL}/query", json=payload)
        response.raise_for_status()
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {data.get('answer_text')[:100]}...")
        print(f"Source Model: {data.get('sources')[0]['model'] if data.get('sources') else 'N/A'}") # Just checking if we can identify it, though API doesn't return model name in sources.
        return True
    except Exception as e:
        print(f"Error: {e}")
        if response:
            print(f"Response Body: {response.text}")
        return False

if __name__ == "__main__":
    query = "What is the filing deadline for 2023 taxes?"
    
    print("Verifying Multi-Model Support...")
    
    # Test SLM
    slm_success = test_model("slm", query)
    
    # Test LLM
    llm_success = test_model("llm", query)
    
    if slm_success and llm_success:
        print("\nSUCCESS: Both models responded.")
        sys.exit(0)
    else:
        print("\nFAILURE: One or both models failed.")
        sys.exit(1)
