#!/usr/bin/env python3
"""Test script to verify multi-model support (Gemini LLM vs Ollama SLM)"""
import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def test_query(model_name, query, description):
    """Test a single query against specified model"""
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"MODEL: {model_name.upper()}")
    print(f"QUERY: {query}")
    print(f"{'='*80}\n")
    
    payload = {
        "query": query,
        "model": model_name
    }
    
    try:
        response = requests.post(f"{BASE_URL}/query", json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Confidence: {data.get('confidence', 'N/A')}")
        print(f"✓ Answer:\n{data.get('answer_text', 'No answer')}\n")
        
        sources = data.get('sources', [])
        if sources:
            print(f"✓ Sources: {len(sources)} found")
            for i, src in enumerate(sources[:2], 1):  # Show first 2
                print(f"  {i}. {src.get('title', 'N/A')[:60]}... (score: {src.get('score', 0):.3f})")
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"✗ ERROR: Request timed out after 60s")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"✗ ERROR: Connection failed - {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        if 'response' in locals():
            print(f"  Response: {response.text[:200]}")
        return False

def main():
    print("\n" + "="*80)
    print("MULTI-MODEL VERIFICATION TEST")
    print("Testing SLM (Ollama) vs LLM (Gemini)")
    print("="*80)
    
    # Test queries
    test_cases = [
        {
            "query": "What is the standard deduction for 2023?",
            "description": "Tax query - Standard deduction"
        },
        {
            "query": "How do I file my taxes?",
            "description": "General tax filing question"
        }
    ]
    
    results = {"slm": [], "llm": []}
    
    # Test each query with both models
    for test in test_cases:
        # Test with SLM (Ollama)
        success = test_query("slm", test["query"], test["description"])
        results["slm"].append(success)
        
        # Test with LLM (Gemini)
        success = test_query("llm", test["query"], test["description"])
        results["llm"].append(success)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"SLM (Ollama): {sum(results['slm'])}/{len(results['slm'])} tests passed")
    print(f"LLM (Gemini):  {sum(results['llm'])}/{len(results['llm'])} tests passed")
    print(f"{'='*80}\n")
    
    return 0 if all(results['slm']) and all(results['llm']) else 1

if __name__ == "__main__":
    sys.exit(main())
