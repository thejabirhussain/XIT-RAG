#!/usr/bin/env python3
"""
Simple Gemini API test to verify credentials and find correct model name
"""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
    
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"API Key loaded: {api_key[:20]}..." if api_key else "No API key found")
    
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set in .env")
        exit(1)
    
    # Configure with API key
    genai.configure(api_key=api_key)
    print("✓ API configured")
    
    # Try creating a model
    print("\nTrying gemini-pro...")
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Say 'Hello' in one word")
        print(f"✓ Success! Response: {response.text}")
    except Exception as e:
        print(f"✗ gemini-pro failed: {e}")
    
    # Try gemini-1.5-flash
    print("\nTrying gemini-1.5-flash...")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'Hello' in one word")
        print(f"✓ Success! Response: {response.text}")
    except Exception as e:
        print(f"✗ gemini-1.5-flash failed: {e}")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
