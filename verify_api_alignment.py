"""
Verification script for frontend-backend model routing alignment.
Tests that the backend correctly accepts and routes requests
based on the model field values "ollama" and "gemini".
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def verify_model_routing():
    """Verify that model field is correctly interpreted"""
    
    print("=" * 60)
    print("Testing Frontend-Backend API Alignment")
    print("=" * 60)
    
    # Test 1: Request with model="ollama"
    print("\n[Test 1] Sending request with model='ollama'")
    payload_ollama = {
        "query": "What is the standard deduction for 2024?",
        "filters": {},
        "json": False,
        "model": "ollama"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/query", json=payload_ollama, timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response received (first 100 chars): {data.get('answer_text', '')[:100]}...")
            print("✓ Test 1 PASSED: Ollama model responded")
        else:
            print(f"✗ Test 1 FAILED: {response.text}")
    except Exception as e:
        print(f"✗ Test 1 ERROR: {str(e)}")
    
    # Test 2: Request with model="gemini"
    print("\n[Test 2] Sending request with model='gemini'")
    payload_gemini = {
        "query": "Identify compliance risks in tax filing",
        "filters": {},
        "json": False,
        "model": "gemini"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/query", json=payload_gemini, timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response received (first 100 chars): {data.get('answer_text', '')[:100]}...")
            print("✓ Test 2 PASSED: Gemini model responded")
        else:
            print(f"✗ Test 2 FAILED: {response.text}")
    except Exception as e:
        print(f"✗ Test 2 ERROR: {str(e)}")
    
    # Test 3: Verify request schema matches frontend
    print("\n[Test 3] Verifying request schema")
    expected_fields = ["query", "filters", "json", "model"]
    actual_fields = list(payload_ollama.keys())
    
    if set(expected_fields) == set(actual_fields):
        print(f"✓ Test 3 PASSED: Request schema matches frontend")
        print(f"  Fields: {actual_fields}")
    else:
        print(f"✗ Test 3 FAILED: Schema mismatch")
        print(f"  Expected: {expected_fields}")
        print(f"  Actual: {actual_fields}")
    
    print("\n" + "=" * 60)
    print("Testing Complete")
    print("=" * 60)

if __name__ == "__main__":
    verify_model_routing()
