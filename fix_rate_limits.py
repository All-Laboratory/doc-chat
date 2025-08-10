#!/usr/bin/env python3
"""
Quick fix for rate limit issues - Set up correct no-retry system
"""

import os
import shutil
from datetime import datetime

def backup_env():
    """Backup current .env file"""
    if os.path.exists(".env"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f".env.backup_{timestamp}"
        shutil.copy(".env", backup_name)
        print(f"✅ Backed up current .env to {backup_name}")

def update_env_file():
    """Update .env file with correct configuration"""
    print("🔧 Updating .env file...")
    
    # Read user's current API keys if they exist
    current_groq_key = None
    current_together_key = None
    current_pinecone_key = None
    current_pinecone_host = None
    
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("TOGETHER_API_KEY=") and "d681c57e" in line:
                    current_together_key = "d681c57e9e5103697f72eccac56df183b76a1f15dbfbcaf39120dd298dbd7fd1"
                elif line.startswith("GROQ_API_KEY=") and not "your_actual" in line:
                    current_groq_key = line.split("=")[1].strip()
                elif line.startswith("PINECONE_API_KEY=") and not "your_pinecone" in line:
                    current_pinecone_key = line.split("=")[1].strip()
                elif line.startswith("PINECONE_INDEX_HOST=") and "pinecone.io" in line:
                    current_pinecone_host = line.split("=")[1].strip()
    
    # Create new .env content
    env_content = f"""# NO-RETRY SYSTEM CONFIGURATION
# CRITICAL: Replace placeholder Groq keys with your actual 3 keys

# =============================================================================
# MULTIPLE GROQ API KEYS (REPLACE WITH YOUR ACTUAL KEYS)
# =============================================================================
GROQ_API_KEY={current_groq_key or "gsk_YOUR_FIRST_ACTUAL_GROQ_KEY_HERE"}
GROQ_API_KEY_2=gsk_YOUR_SECOND_ACTUAL_GROQ_KEY_HERE
GROQ_API_KEY_3=gsk_YOUR_THIRD_ACTUAL_GROQ_KEY_HERE
GROQ_MODEL=llama3-8b-8192

# =============================================================================
# TOGETHER AI (Fallback)
# =============================================================================
TOGETHER_API_KEY={current_together_key or "d681c57e9e5103697f72eccac56df183b76a1f15dbfbcaf39120dd298dbd7fd1"}
TOGETHER_MODEL=moonshotai/kimi-k2-instruct

# =============================================================================
# EMBEDDING MODEL (Required)
# =============================================================================
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DIMENSIONS=384

# =============================================================================
# PINECONE (Required)
# =============================================================================
USE_CLOUD_RETRIEVER=true
PINECONE_API_KEY={current_pinecone_key or "your_pinecone_api_key_here"}
PINECONE_INDEX_NAME=document-reasoning
PINECONE_INDEX_HOST={current_pinecone_host or "your_pinecone_host_here"}
PINECONE_NAMESPACE=default

# =============================================================================
# OPTIMIZATION SETTINGS
# =============================================================================
CHUNK_SIZE=800
CHUNK_OVERLAP=100
TOP_K_RESULTS=3
LOG_LEVEL=INFO
"""
    
    # Write new .env file
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Updated .env file with no-retry configuration")

def check_main_py():
    """Check if main.py is using no-retry system"""
    main_py_path = "app/main.py"
    
    if not os.path.exists(main_py_path):
        print(f"❌ {main_py_path} not found")
        return False
    
    with open(main_py_path, "r") as f:
        content = f.read()
    
    if "llm_utils_no_retry" in content:
        print("✅ main.py is already using no-retry system")
        return True
    else:
        print("❌ main.py is NOT using no-retry system")
        return False

def main():
    """Main fix function"""
    print("🚨 RATE LIMIT FIX SCRIPT")
    print("=" * 50)
    
    print("\n🔍 Diagnosing issues...")
    
    # Check current state
    issues = []
    
    # Check if using no-retry system
    if not check_main_py():
        issues.append("Not using no-retry system")
    
    # Check .env file
    env_issues = []
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            env_content = f.read()
        
        if "GROQ_API_KEY_2" not in env_content:
            env_issues.append("Missing GROQ_API_KEY_2")
        if "GROQ_API_KEY_3" not in env_content:
            env_issues.append("Missing GROQ_API_KEY_3")
        if "your_actual_groq_api_key_here" in env_content:
            env_issues.append("Using placeholder Groq keys")
        if "LLM_PROVIDER=together" in env_content:
            env_issues.append("Wrong LLM_PROVIDER (should use no-retry system)")
    else:
        env_issues.append("No .env file found")
    
    if env_issues:
        issues.extend(env_issues)
    
    if issues:
        print(f"\n🚨 Found {len(issues)} issues:")
        for issue in issues:
            print(f"   ❌ {issue}")
    else:
        print("\n✅ Configuration looks good!")
    
    # Ask if user wants to fix
    if issues:
        print(f"\n🔧 Do you want to fix these issues? (y/n): ", end="")
        response = input().strip().lower()
        
        if response in ['y', 'yes']:
            print(f"\n🛠️ Fixing issues...")
            
            # Backup and update .env
            backup_env()
            update_env_file()
            
            print(f"\n✅ FIXES APPLIED!")
            print(f"\n🚨 IMPORTANT: You still need to:")
            print(f"1. Replace the placeholder Groq API keys in .env with your actual 3 keys")
            print(f"2. Get keys from: https://console.groq.com")
            print(f"3. Create 3 separate Groq accounts for 3 API keys")
            print(f"4. Add your Pinecone API key if not already set")
            
            print(f"\n🧪 Run this command to test your keys:")
            print(f"   python test_groq_keys.py")
            
        else:
            print("Skipped fixes.")
    
    print(f"\n📝 Manual steps to eliminate rate limits:")
    print(f"1. Get 3 Groq API keys from https://console.groq.com")
    print(f"2. Replace placeholders in .env with actual keys")
    print(f"3. Test with: python test_groq_keys.py")
    print(f"4. Your app will have 90 requests/minute (no rate limits)")

if __name__ == "__main__":
    main()
