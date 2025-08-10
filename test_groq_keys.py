#!/usr/bin/env python3
"""
Test script to verify your multiple Groq API keys work correctly
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_groq_key(api_key, key_name):
    """Test a single Groq API key"""
    print(f"\n🧪 Testing {key_name}...")
    
    if not api_key or api_key in ["your_actual_groq_api_key_here", "gsk_replace_with_your_first_actual_groq_key"]:
        print(f"❌ {key_name}: Invalid/placeholder key")
        return False
    
    if not api_key.startswith("gsk_"):
        print(f"❌ {key_name}: Key should start with 'gsk_'")
        return False
    
    # Test API call
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"].strip()
            print(f"✅ {key_name}: Working! Response: {answer}")
            return True
        elif response.status_code == 401:
            print(f"❌ {key_name}: Invalid API key (401)")
            return False
        elif response.status_code == 429:
            print(f"⚠️ {key_name}: Rate limited (429) - but key is valid")
            return True  # Key works, just rate limited
        else:
            print(f"❌ {key_name}: Error {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {key_name}: Connection error - {str(e)}")
        return False

def test_no_retry_system():
    """Test if the no-retry system is being used"""
    print(f"\n🔍 Checking if no-retry system is active...")
    
    try:
        from app.llm_utils_no_retry import DocumentReasoningLLM
        print("✅ No-retry system is imported correctly")
        
        # Test initialization
        llm = DocumentReasoningLLM()
        
        # Check how many Groq keys were loaded
        groq_count = len(llm.groq_multi.providers)
        print(f"✅ Found {groq_count} working Groq API keys")
        
        if groq_count == 0:
            print("❌ No Groq keys were loaded!")
            return False
        elif groq_count < 3:
            print(f"⚠️ Only {groq_count} Groq keys loaded (expected 3)")
        else:
            print("🎉 All 3 Groq keys loaded successfully!")
        
        return True
        
    except ImportError:
        print("❌ No-retry system not found - are you using the old system?")
        return False
    except Exception as e:
        print(f"❌ Error testing no-retry system: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 GROQ MULTI-KEY TEST")
    print("=" * 50)
    
    # Test individual keys
    keys_to_test = [
        ("GROQ_API_KEY", os.getenv("GROQ_API_KEY")),
        ("GROQ_API_KEY_2", os.getenv("GROQ_API_KEY_2")),
        ("GROQ_API_KEY_3", os.getenv("GROQ_API_KEY_3"))
    ]
    
    working_keys = 0
    for key_name, api_key in keys_to_test:
        if test_groq_key(api_key, key_name):
            working_keys += 1
    
    print(f"\n📊 RESULTS:")
    print(f"Working keys: {working_keys}/3")
    
    if working_keys == 0:
        print("🚨 No working Groq keys found!")
        print("\n💡 FIX: Replace placeholder keys in .env with actual Groq API keys")
        print("Get keys from: https://console.groq.com")
    elif working_keys < 3:
        print(f"⚠️ Only {working_keys} keys working - you'll have reduced capacity")
    else:
        print("🎉 All keys working! You have 90 requests/minute capacity")
    
    # Test no-retry system
    if test_no_retry_system():
        if working_keys > 0:
            print("\n✅ SYSTEM STATUS: Ready for no-retry operation!")
        else:
            print("\n❌ SYSTEM STATUS: Need valid API keys")
    else:
        print("\n❌ SYSTEM STATUS: No-retry system not active")
    
    print(f"\n📝 Next steps:")
    if working_keys == 0:
        print("1. Add your actual Groq API keys to .env")
        print("2. Run this test again")
    elif working_keys < 3:
        print("1. Add more Groq API keys for higher capacity")
        print("2. Test your document chat application")
    else:
        print("1. Test your document chat application") 
        print("2. You should see 1-3 second responses with no 429 errors")

if __name__ == "__main__":
    main()
