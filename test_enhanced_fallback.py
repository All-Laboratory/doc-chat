#!/usr/bin/env python3
"""
Test script for the enhanced LLM fallback system with rate limit handling.
This demonstrates how the system handles rate limits and automatically falls back to other providers.
"""

import os
import json
import time
from app.llm_utils_enhanced_fallback import DocumentReasoningLLM

def setup_test_environment():
    """Setup test environment variables"""
    # You can set your actual API keys here or in .env file
    # For testing purposes, you can use placeholder values
    
    # Example environment setup (replace with your actual keys)
    # os.environ["TOGETHER_API_KEY"] = "your_actual_together_key"
    # os.environ["GROQ_API_KEY"] = "your_actual_groq_key"
    # os.environ["OPENAI_API_KEY"] = "your_actual_openai_key"
    # os.environ["FIREWORKS_API_KEY"] = "your_actual_fireworks_key"
    
    # Model configurations
    os.environ["TOGETHER_MODEL"] = "moonshotai/kimi-k2-instruct"
    os.environ["GROQ_MODEL"] = "llama3-8b-8192"
    os.environ["OPENAI_MODEL"] = "gpt-3.5-turbo"
    os.environ["FIREWORKS_MODEL"] = "accounts/fireworks/models/llama-v2-7b-chat"
    
    # Set primary provider
    os.environ["LLM_PROVIDER"] = "together"

def create_sample_document_chunks():
    """Create sample document chunks for testing"""
    return [
        {
            "clause_id": "Section 3.1 - Coverage",
            "text": "This policy provides coverage for accidental injuries and illnesses that occur during the policy period. Coverage includes emergency medical treatment, hospitalization, and rehabilitation services.",
            "similarity_score": 0.89
        },
        {
            "clause_id": "Section 3.2 - Exclusions", 
            "text": "This policy does not cover pre-existing medical conditions, cosmetic procedures, or injuries resulting from illegal activities. Mental health services are covered only for conditions directly related to covered accidents.",
            "similarity_score": 0.76
        },
        {
            "clause_id": "Section 4.1 - Claims Process",
            "text": "To file a claim, contact our claims department within 30 days of the incident. Provide all relevant medical documentation and receipts. Claims are typically processed within 14 business days.",
            "similarity_score": 0.82
        }
    ]

def test_basic_functionality():
    """Test basic functionality with mock data"""
    print("🧪 Testing Enhanced LLM Fallback System")
    print("=" * 50)
    
    try:
        # Initialize the enhanced LLM system
        llm = DocumentReasoningLLM()
        
        # Display provider status
        print("\n📊 Provider Status:")
        status = llm.get_provider_status()
        for provider_name, provider_status in status.items():
            available = "✅ Available" if provider_status["available"] else "❌ Not Available"
            rate_limited = "🚦 Rate Limited" if provider_status["rate_limited"] else "✅ No Rate Limit"
            model = provider_status["model"]
            print(f"  {provider_name.capitalize()}: {available} | {rate_limited} | Model: {model}")
        
        # Test with sample query
        print("\n🔍 Testing Document Query Analysis...")
        query = "Does this policy cover emergency medical treatment?"
        chunks = create_sample_document_chunks()
        
        print(f"Query: {query}")
        print("\nProcessing with fallback system...")
        
        start_time = time.time()
        result = llm.analyze_document_query(query, chunks)
        processing_time = time.time() - start_time
        
        print(f"\n✅ Response received in {processing_time:.2f} seconds")
        print(f"Direct Answer: {result['direct_answer']}")
        print(f"Decision: {result['decision']}")
        print(f"Justification: {result['justification'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_rate_limit_simulation():
    """Test the system's behavior with simulated rate limits"""
    print("\n🚦 Testing Rate Limit Handling")
    print("-" * 40)
    
    try:
        llm = DocumentReasoningLLM()
        
        # Simulate rate limiting on primary provider
        if llm.primary_provider:
            print(f"Simulating rate limit on primary provider: {llm.primary_provider_name}")
            llm.primary_provider.mark_rate_limited()
            
            print(f"Primary provider is now rate limited: {llm.primary_provider.is_rate_limited()}")
            
            # Show available providers after rate limiting
            available_providers = llm._get_available_providers()
            print(f"Available providers after rate limit: {[name for name, _ in available_providers]}")
            
            # Test query with rate-limited primary
            query = "What are the exclusions in this policy?"
            chunks = create_sample_document_chunks()
            
            print("\nTesting query with rate-limited primary provider...")
            result = llm.analyze_document_query(query, chunks)
            
            print(f"✅ Fallback successful!")
            print(f"Direct Answer: {result['direct_answer']}")
            
        return True
        
    except Exception as e:
        print(f"❌ Rate limit test failed: {str(e)}")
        return False

def test_provider_status_monitoring():
    """Test provider status monitoring functionality"""
    print("\n📈 Testing Provider Status Monitoring")
    print("-" * 40)
    
    try:
        llm = DocumentReasoningLLM()
        
        # Get initial status
        initial_status = llm.get_provider_status()
        print("Initial Provider Status:")
        print(json.dumps(initial_status, indent=2, default=str))
        
        # Simulate some failures
        if llm.primary_provider:
            llm.primary_provider.consecutive_failures = 2
            llm.primary_provider.mark_rate_limited()
        
        # Get updated status
        updated_status = llm.get_provider_status()
        print("\nUpdated Provider Status (after simulated failures):")
        print(json.dumps(updated_status, indent=2, default=str))
        
        return True
        
    except Exception as e:
        print(f"❌ Monitoring test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Enhanced LLM Fallback System Test Suite")
    print("=" * 60)
    
    # Setup environment
    setup_test_environment()
    
    # Run tests
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Rate Limit Handling", test_rate_limit_simulation),
        ("Status Monitoring", test_provider_status_monitoring)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name} Test...")
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n📋 Test Results Summary")
    print("=" * 40)
    passed = 0
    for test_name, passed_test in results:
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name}: {status}")
        if passed_test:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The enhanced fallback system is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check your API keys and configuration.")
    
    print("\n💡 Tips for Production:")
    print("- Set your actual API keys in environment variables or .env file")
    print("- Monitor provider status regularly using get_provider_status()")
    print("- The system automatically handles rate limits and fails over to available providers")
    print("- Rate-limited providers are automatically excluded for 60 seconds")
    print("- Providers with 3+ consecutive failures are temporarily disabled")

if __name__ == "__main__":
    main()
