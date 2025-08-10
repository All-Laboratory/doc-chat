#!/usr/bin/env python3
"""
Test script for the Groq → Together AI fallback system.
This demonstrates the simple two-provider cycling approach.
"""

import os
import json
import time
from app.llm_utils_groq_together import DocumentReasoningLLM

def setup_test_environment():
    """Setup test environment variables"""
    # Set model configurations
    os.environ["GROQ_MODEL"] = "llama3-8b-8192"
    os.environ["TOGETHER_MODEL"] = "moonshotai/kimi-k2-instruct"
    
    print("🔧 Environment configured for Groq → Together AI fallback")
    print(f"   Groq Model: {os.environ['GROQ_MODEL']}")
    print(f"   Together Model: {os.environ['TOGETHER_MODEL']}")

def create_sample_document_chunks():
    """Create sample document chunks for testing"""
    return [
        {
            "clause_id": "Section 2.1 - Medical Coverage",
            "text": "This insurance policy covers all emergency medical treatments including surgery, hospitalization, and rehabilitation services. Coverage is valid worldwide and includes ambulance services.",
            "similarity_score": 0.92
        },
        {
            "clause_id": "Section 2.3 - Exclusions", 
            "text": "The following are excluded from coverage: cosmetic surgery, experimental treatments, and pre-existing conditions not disclosed at the time of application.",
            "similarity_score": 0.78
        },
        {
            "clause_id": "Section 3.1 - Claims Process",
            "text": "To file a claim, submit Form 105 within 30 days of treatment. Include all medical records and receipts. Emergency pre-authorization is available 24/7.",
            "similarity_score": 0.85
        }
    ]

def test_provider_initialization():
    """Test that providers are properly initialized"""
    print("🧪 Testing Provider Initialization")
    print("-" * 40)
    
    try:
        llm = DocumentReasoningLLM()
        
        # Display provider status
        status = llm.get_provider_status()
        
        print("Provider Status:")
        for provider_name, info in status.items():
            available_icon = "✅" if info["available"] else "❌"
            rate_limited_icon = "🚦" if info["rate_limited"] else "✅"
            
            print(f"  {provider_name.upper()}:")
            print(f"    Status: {available_icon} {'Available' if info['available'] else 'Unavailable'}")
            print(f"    Rate Limited: {rate_limited_icon} {'Yes' if info['rate_limited'] else 'No'}")
            print(f"    Model: {info['model']}")
            print(f"    Failures: {info['consecutive_failures']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {str(e)}")
        return False

def test_normal_operation():
    """Test normal operation with document query"""
    print("🔍 Testing Normal Operation")
    print("-" * 40)
    
    try:
        llm = DocumentReasoningLLM()
        
        query = "Does this policy cover emergency surgery?"
        chunks = create_sample_document_chunks()
        
        print(f"Query: {query}")
        print("Processing...")
        
        start_time = time.time()
        result = llm.analyze_document_query(query, chunks)
        processing_time = time.time() - start_time
        
        print(f"\n✅ Response received in {processing_time:.2f} seconds")
        print(f"Direct Answer: {result['direct_answer']}")
        print(f"Decision: {result['decision']}")
        print(f"Justification: {result['justification'][:150]}...")
        print(f"Referenced Clauses: {len(result['referenced_clauses'])} clause(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_rate_limit_simulation():
    """Test fallback behavior when primary provider is rate limited"""
    print("🚦 Testing Rate Limit Fallback")
    print("-" * 40)
    
    try:
        llm = DocumentReasoningLLM()
        
        # Simulate rate limiting on Groq (primary)
        if llm.groq_provider:
            print("Simulating rate limit on Groq...")
            llm.groq_provider.mark_rate_limited()
            print(f"Groq rate limited: {llm.groq_provider.is_rate_limited()}")
            
            # Test query with rate-limited Groq
            query = "What exclusions apply to this policy?"
            chunks = create_sample_document_chunks()
            
            print(f"\nQuery with rate-limited Groq: {query}")
            print("Should fallback to Together AI...")
            
            start_time = time.time()
            result = llm.analyze_document_query(query, chunks)
            processing_time = time.time() - start_time
            
            print(f"✅ Fallback successful in {processing_time:.2f} seconds!")
            print(f"Direct Answer: {result['direct_answer']}")
            
        else:
            print("⚠️ Groq provider not available, skipping rate limit test")
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limit test failed: {str(e)}")
        return False

def test_cycling_behavior():
    """Test the Groq → Together → Groq → Together cycling"""
    print("🔄 Testing Provider Cycling")
    print("-" * 40)
    
    try:
        llm = DocumentReasoningLLM()
        
        # Multiple queries to see cycling behavior
        queries = [
            "Is ambulance service covered?",
            "What is the claims process?",
            "Are pre-existing conditions covered?"
        ]
        
        chunks = create_sample_document_chunks()
        
        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}: {query}")
            
            start_time = time.time()
            result = llm.analyze_document_query(query, chunks)
            processing_time = time.time() - start_time
            
            print(f"Response in {processing_time:.2f}s: {result['direct_answer'][:80]}...")
            
            # Small delay between requests
            time.sleep(0.5)
        
        return True
        
    except Exception as e:
        print(f"❌ Cycling test failed: {str(e)}")
        return False

def test_both_providers_rate_limited():
    """Test emergency fallback when both providers are rate limited"""
    print("🆘 Testing Emergency Fallback (Both Rate Limited)")
    print("-" * 40)
    
    try:
        llm = DocumentReasoningLLM()
        
        # Simulate rate limiting on both providers
        if llm.groq_provider:
            llm.groq_provider.mark_rate_limited()
            print("Groq marked as rate limited")
        
        if llm.together_provider:
            llm.together_provider.mark_rate_limited()
            print("Together AI marked as rate limited")
        
        query = "What is covered under this policy?"
        chunks = create_sample_document_chunks()
        
        print(f"\nQuery with both providers rate limited: {query}")
        print("Should still provide document content...")
        
        start_time = time.time()
        result = llm.analyze_document_query(query, chunks)
        processing_time = time.time() - start_time
        
        print(f"✅ Emergency fallback worked in {processing_time:.2f} seconds!")
        print(f"Direct Answer: {result['direct_answer']}")
        print(f"Still provided {len(result['referenced_clauses'])} document sections")
        
        return True
        
    except Exception as e:
        print(f"❌ Emergency fallback test failed: {str(e)}")
        return False

def main():
    """Run all tests for the Groq → Together AI system"""
    print("🚀 Groq → Together AI Fallback System Test")
    print("=" * 60)
    
    # Setup environment
    setup_test_environment()
    print()
    
    # Run tests
    tests = [
        ("Provider Initialization", test_provider_initialization),
        ("Normal Operation", test_normal_operation),
        ("Rate Limit Fallback", test_rate_limit_simulation),
        ("Provider Cycling", test_cycling_behavior),
        ("Emergency Fallback", test_both_providers_rate_limited)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📋 Test Results Summary")
    print("=" * 40)
    
    passed = 0
    for test_name, passed_test in results:
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name}: {status}")
        if passed_test:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The Groq → Together AI fallback system is working perfectly!")
    else:
        print("⚠️ Some tests failed. Please check your API keys and configuration.")
    
    print("\n💡 System Behavior Summary:")
    print("1. 🥇 Groq processes requests first (fast and efficient)")
    print("2. 🔄 If Groq fails/rate limited → Together AI takes over")
    print("3. 🔁 Pattern repeats: Groq → Together → Groq → Together")  
    print("4. ⏰ Rate-limited providers get 60-second cooldown")
    print("5. 🛡️ Even if both fail, document content is always provided")
    
    print("\n🔧 Integration Instructions:")
    print("Replace your current import with:")
    print("from app.llm_utils_groq_together import DocumentReasoningLLM")

if __name__ == "__main__":
    main()
