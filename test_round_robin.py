#!/usr/bin/env python3
"""
Test script for round-robin LLM implementation
"""

import requests
import json
import time

def test_round_robin_api():
    """Test the round-robin API with a sample document and questions"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Round-Robin LLM Implementation")
    print("=" * 50)
    
    # Test 1: Basic health check
    print("\n1. Testing basic connectivity...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is running - Mode: {data.get('mode', 'unknown')}")
        else:
            print(f"❌ API returned status: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return
    
    # Test 2: Test hackrx endpoint with sample data
    print("\n2. Testing hackrx endpoint with round-robin LLM...")
    
    # Sample request data - using a simple text document
    test_data = {
        "documents": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "questions": [
            "What is the main content of this document?",
            "What type of document is this?"
        ]
    }
    
    headers = {
        "Authorization": "Bearer 6be388e87eae07a6e1ee672992bc2a22f207bbc7ff7e043758105f7d1fa45ffd",
        "Content-Type": "application/json"
    }
    
    try:
        print("📤 Sending test request...")
        start_time = time.time()
        
        response = requests.post(
            f"{base_url}/hackrx/run",
            json=test_data,
            headers=headers,
            timeout=60
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            answers = data.get("answers", [])
            print(f"✅ Request successful! Got {len(answers)} answers")
            
            # Display answers
            for i, (question, answer) in enumerate(zip(test_data["questions"], answers), 1):
                print(f"\n📝 Q{i}: {question}")
                print(f"🤖 A{i}: {answer[:200]}{'...' if len(answer) > 200 else ''}")
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_round_robin_api()
