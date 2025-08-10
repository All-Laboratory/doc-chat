#!/usr/bin/env python3
"""
Debug script to check which Railway Groq keys are working
Run this on Railway to see which keys are being loaded
"""

import os
import requests
import json
from typing import List, Tuple

def test_single_key(api_key: str, key_name: str) -> bool:
    """Test a single Groq API key"""
    if not api_key or api_key in ["your_actual_groq_api_key_here", "gsk_replace", ""]:
        print(f"❌ {key_name}: Empty or placeholder key")
        return False
    
    if not api_key.startswith("gsk_"):
        print(f"❌ {key_name}: Invalid format (should start with 'gsk_')")
        return False
    
    # Test with a minimal API call
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 5,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            print(f"✅ {key_name}: WORKING - Key is valid")
            return True
        elif response.status_code == 401:
            print(f"❌ {key_name}: INVALID - Authentication failed (401)")
            return False
        elif response.status_code == 429:
            print(f"⚠️ {key_name}: RATE LIMITED - But key is valid (429)")
            return True  # Key works, just rate limited
        else:
            print(f"❌ {key_name}: ERROR {response.status_code} - {response.text[:100]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ {key_name}: TIMEOUT - Network issue, but key might be valid")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {key_name}: CONNECTION ERROR - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ {key_name}: UNEXPECTED ERROR - {str(e)}")
        return False

def check_environment_variables():
    """Check which environment variables are set"""
    print("🔍 CHECKING RAILWAY ENVIRONMENT VARIABLES:")
    print("=" * 50)
    
    env_vars = [
        "GROQ_API_KEY",
        "GROQ_API_KEY_2", 
        "GROQ_API_KEY_3",
        "GROQ_MODEL",
        "TOGETHER_API_KEY",
        "TOGETHER_MODEL"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if "gsk_" in var.lower():
                # Mask API keys for security
                masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                print(f"✅ {var} = {masked}")
            else:
                print(f"✅ {var} = {value}")
        else:
            print(f"❌ {var} = NOT SET")
    
    print()

def test_all_groq_keys():
    """Test all Groq API keys"""
    print("🧪 TESTING GROQ API KEYS:")
    print("=" * 50)
    
    keys_to_test = [
        ("GROQ_API_KEY", os.getenv("GROQ_API_KEY")),
        ("GROQ_API_KEY_2", os.getenv("GROQ_API_KEY_2")),
        ("GROQ_API_KEY_3", os.getenv("GROQ_API_KEY_3"))
    ]
    
    working_keys = 0
    invalid_keys = []
    
    for key_name, api_key in keys_to_test:
        print(f"\n🔑 Testing {key_name}:")
        if test_single_key(api_key, key_name):
            working_keys += 1
        else:
            invalid_keys.append(key_name)
    
    print(f"\n📊 RESULTS:")
    print(f"✅ Working keys: {working_keys}/3")
    if invalid_keys:
        print(f"❌ Invalid keys: {', '.join(invalid_keys)}")
    
    return working_keys, invalid_keys

def simulate_no_retry_system():
    """Simulate what the no-retry system would do"""
    print("\n🔄 SIMULATING NO-RETRY SYSTEM:")
    print("=" * 50)
    
    try:
        # Try to import and initialize the system (like Railway would)
        keys = []
        for i in range(1, 4):
            key_name = f"GROQ_API_KEY_{i}" if i > 1 else "GROQ_API_KEY"
            key = os.getenv(key_name)
            if key and key not in ["your_actual_groq_api_key_here", ""]:
                keys.append((key_name, key))
        
        print(f"📋 Found {len(keys)} potential keys in environment")
        
        # Test which ones would be loaded
        valid_keys = 0
        for key_name, key in keys:
            if test_single_key(key, f"Loading {key_name}"):
                valid_keys += 1
        
        print(f"\n🎯 NO-RETRY SYSTEM WOULD LOAD: {valid_keys} keys")
        
        if valid_keys == 0:
            print("🚨 CRITICAL: No working keys - system would fail!")
        elif valid_keys < 3:
            print(f"⚠️ WARNING: Only {valid_keys} keys working - reduced capacity")
        else:
            print("🎉 PERFECT: All 3 keys working - full capacity!")
        
        return valid_keys
        
    except Exception as e:
        print(f"❌ ERROR simulating system: {str(e)}")
        return 0

def main():
    """Main debug function"""
    print("🚂 RAILWAY GROQ KEYS DEBUG")
    print("=" * 60)
    print("This script helps debug why Railway shows only 2/3 keys")
    print()
    
    # Check environment variables
    check_environment_variables()
    
    # Test all keys
    working_keys, invalid_keys = test_all_groq_keys()
    
    # Simulate the system
    system_keys = simulate_no_retry_system()
    
    # Provide recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("=" * 50)
    
    if working_keys == 3:
        print("✅ All 3 keys are valid - there might be a code issue")
        print("   Check Railway logs for import errors")
    elif working_keys == 2:
        print(f"🔧 1 key is invalid: {invalid_keys}")
        print("   Fix the invalid key in Railway environment variables")
    elif working_keys == 1:
        print(f"🔧 2 keys are invalid: {invalid_keys}")
        print("   Fix the invalid keys in Railway environment variables")
    elif working_keys == 0:
        print("🚨 All keys are invalid!")
        print("   Check if keys are correctly set in Railway dashboard")
    
    print(f"\n📝 NEXT STEPS:")
    if invalid_keys:
        print(f"1. Go to Railway Dashboard → Variables")
        print(f"2. Check these keys: {', '.join(invalid_keys)}")
        print(f"3. Make sure they start with 'gsk_'")
        print(f"4. Verify they're from different Groq accounts")
        print(f"5. Test keys at https://console.groq.com")
    else:
        print(f"1. All keys seem valid - check Railway deployment logs")
        print(f"2. Look for 'NO-RETRY LLM System initialized'")
        print(f"3. Check for any import or initialization errors")

if __name__ == "__main__":
    main()
