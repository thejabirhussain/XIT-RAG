#!/usr/bin/env python3
"""Try multiple Gemini model names"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

models = [
    ("v1", "gemini-1.5-pro"),
    ("v1", "gemini-2.0-flash-exp"),
    ("v1beta", "gemini-1.5-pro"),
    ("v1beta", "gemini-2.0-flash-exp"),
    ("v1beta", "gemini-exp-1206"),
]

payload = {
    "contents": [{
        "parts": [{"text": "Reply with just the number: 2+2=?"}]
    }]
}

for api_ver, model in models:
    url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model}:generateContent?key={api_key}"
    print(f"\nTrying {api_ver}/{model}...")
    response = requests.post(url, json=payload)
    if response.ok:
        data = response.json()
        text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No text')
        print(f"  ✓ SUCCESS! Response: {text.strip()}")
        break
    else:
        print(f"  ✗ Failed ({response.status_code})")
