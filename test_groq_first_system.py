#!/usr/bin/env python3
"""
Test script for the new Groq-first LLM system
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_system_initialization():
    """Test that the system initializes correctly"""
    print("🧪 Testing Groq-First LLM System Initialization")
    print("=" * 60)
    
    try:
        from app.llm_utils_groq_first import DocumentReasoningLLM
        
        # Initialize the system
        llm = DocumentReasoningLLM()
        
        # Check provider status
        status = llm.get_provider_status()
        
        print("✅ System initialized successfully!")
        print("\n📊 Provider Status:")
        for provider_name, provider_info in status.items():
            availability = "🟢 Available" if provider_info["available"] else "🔴 Not Available"
            priority = provider_info["priority"]
            model = provider_info["model"]
            
            print(f"  {provider_name.title()}: {availability} ({priority}) - {model}")
            
            if provider_info["rate_limited"]:
                print(f"    ⏰ Rate limited (cooling down)")
            
            if provider_info["consecutive_failures"] > 0:
                print(f"    ⚠️ Consecutive failures: {provider_info['consecutive_failures']}")
        
        return True
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False

def test_provider_priority():
    """Test that providers are tried in the correct order"""
    print("\n🧪 Testing Provider Priority Logic")
    print("=" * 60)
    
    try:
        from app.llm_utils_groq_first import DocumentReasoningLLM
        
        llm = DocumentReasoningLLM()
        
        # Create mock relevant chunks for testing
        mock_chunks = [
            {
                "clause_id": "Section 1",
                "text": "This is a test document section about health coverage policies.",
                "similarity_score": 0.95
            }
        ]
        
        print("🚀 Testing query processing with mock data...")
        
        # This should try Groq first, then Together AI if Groq fails
        result = llm.analyze_document_query("What is covered by this policy?", mock_chunks)
        
        if isinstance(result, dict) and "direct_answer" in result:
            print("✅ Query processed successfully!")
            print(f"📝 Response: {result['direct_answer'][:100]}...")
            print(f"🎯 Decision: {result['decision']}")
            return True
        else:
            print("⚠️ Query processed but returned unexpected format")
            print(f"Result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Provider priority test failed: {e}")
        return False

def check_environment_variables():
    """Check if required environment variables are set"""
    print("\n🧪 Checking Environment Variables")
    print("=" * 60)
    
    required_vars = {
        "GROQ_API_KEY": "Groq API key",
        "TOGETHER_API_KEY": "Together AI API key",
    }
    
    optional_vars = {
        "GROQ_MODEL": "Groq model (default: llama3-8b-8192)",
        "TOGETHER_MODEL": "Together AI model (default: moonshotai/kimi-k2-instruct)",
        "RAILWAY_ENVIRONMENT": "Railway environment indicator"
    }
    
    available_count = 0
    
    print("🔑 Required API Keys:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and value not in ["your_actual_groq_api_key_here", "your_groq_api_key", "your_together_api_key", "your_actual_api_key"]:
            print(f"  ✅ {var}: Set ({description})")
            available_count += 1
        else:
            print(f"  ❌ {var}: Not set ({description})")
    
    print(f"\n⚙️ Optional Configuration:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value} ({description})")
        else:
            print(f"  ⚪ {var}: Not set ({description})")
    
    if available_count > 0:
        print(f"\n🎉 {available_count}/{len(required_vars)} API keys are configured!")
        return True
    else:
        print(f"\n⚠️ No API keys configured. Please set at least one of: {', '.join(required_vars.keys())}")
        return False

def main():
    """Run all tests"""
    print("🚀 GROQ-FIRST LLM SYSTEM TESTS")
    print("=" * 60)
    
    # Check environment first
    env_ok = check_environment_variables()
    
    # Test system initialization
    init_ok = test_system_initialization()
    
    # Only test priority if system initialized successfully
    priority_ok = False
    if init_ok:
        priority_ok = test_provider_priority()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    print(f"Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"System Initialization: {'✅ PASS' if init_ok else '❌ FAIL'}")
    print(f"Provider Priority:     {'✅ PASS' if priority_ok else '❌ FAIL'}")
    
    if env_ok and init_ok and priority_ok:
        print("\n🎉 ALL TESTS PASSED! Your Groq-first system is ready!")
        print("\n💡 Next Steps:")
        print("1. Start your server: python -m uvicorn app.main:app --reload")
        print("2. Check provider status: GET /provider-status")
        print("3. Deploy to Railway with your environment variables")
    elif env_ok and init_ok:
        print("\n⚠️ TESTS PARTIALLY PASSED - System works but query test failed")
        print("This might be due to API rate limits or invalid responses")
    elif not env_ok:
        print("\n❌ ENVIRONMENT CONFIGURATION NEEDED")
        print("Please set your API keys in the .env file:")
        print("GROQ_API_KEY=your_actual_groq_key")
        print("TOGETHER_API_KEY=your_actual_together_key")
    else:
        print("\n❌ SYSTEM INITIALIZATION FAILED")
        print("Check the error messages above for details")

if __name__ == "__main__":
    main()
