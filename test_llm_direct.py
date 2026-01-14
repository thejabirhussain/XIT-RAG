#!/usr/bin/env python3
"""
Direct test of LLMService multi-model functionality
Bypasses FastAPI to test the core logic directly
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import our service
from services.rag_services.llm_service import LLMService

def test_llm_service():
    """Test LLMService with both Ollama and Gemini"""
    
    print("="*80)
    print("DIRECT LLM SERVICE TEST")
    print("="*80)
    
    # Get configuration
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    print(f"\nConfiguration:")
    print(f"  Ollama Host: {ollama_host}")
    print(f"  Gemini API Key: {'✓ Set' if gemini_api_key else '✗ NOT SET'}")
    print()
    
    # Initialize service
    print("Initializing LLMService...")
    try:
        llm_service = LLMService(ollama_host=ollama_host, gemini_api_key=gemini_api_key)
        print("✓ Service initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return False
    
    # Test prompt
    test_prompt = """You are a helpful assistant. Answer this question briefly:

Question: What is 2+2?

Please provide a one sentence answer."""
    
    # Test 1: SLM (Ollama)
    print("\n" + "="*80)
    print("TEST 1: SLM (Ollama)")
    print("="*80)
    try:
        print("Sending request to Ollama...")
        response = llm_service.generate(
            prompt=test_prompt,
            model_choice="slm",
            temperature=0.0,
            max_tokens=100
        )
        print(f"✓ Response received:")
        print(f"  {response[:200]}")
        if len(response) > 200:
            print(f"  ... ({len(response)} chars total)")
    except Exception as e:
        print(f"✗ SLM test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: LLM (Gemini)
    print("\n" + "="*80)
    print("TEST 2: LLM (Gemini)")
    print("="*80)
    
    if not gemini_api_key:
        print("⚠ SKIPPED: GEMINI_API_KEY not set in .env file")
        print("  Please add: GEMINI_API_KEY=your_key_here")
    else:
        try:
            print("Sending request to Gemini...")
            response = llm_service.generate(
                prompt=test_prompt,
                model_choice="llm",
                temperature=0.0,
                max_tokens=100
            )
            print(f"✓ Response received:")
            print(f"  {response[:200]}")
            if len(response) > 200:
                print(f"  ... ({len(response)} chars total)")
        except Exception as e:
            print(f"✗ LLM test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    
    return True

if __name__ == "__main__":
    success = test_llm_service()
    sys.exit(0 if success else 1)
