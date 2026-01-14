#!/usr/bin/env python3
"""
Test using the REST API directly instead of the deprecated SDK
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key: {api_key[:20]}..." if api_key else "No API key")

# Try current API (v1)
url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}"

payload = {
    "contents": [{
        "parts": [{"text": "Say 'Hello' in one word"}]
    }]
}

print("\nTesting Gemini API directly...")
response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
if response.ok:
    data = response.json()
    text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No text')
    print(f"✓ Response: {text}")
else:
    print(f"✗ Error: {response.text}")

# Try v1beta/gemini-1.5-flash
url2 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
print("\nTrying v1beta/gemini-1.5-flash...")
response2 = requests.post(url2, json=payload)
print(f"Status: {response2.status_code}")
if response2.ok:
    data = response2.json()
    text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No text')
    print(f"✓ Response: {text}")
else:
    print(f"✗ Error: {response2.text[:200]}")
