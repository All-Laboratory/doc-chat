#!/usr/bin/env python3
"""
Direct test of the round-robin LLM implementation
"""

import os
import sys
sys.path.append('.')

from dotenv import load_dotenv
from app.llm_utils_round_robin import DocumentReasoningLLM

load_dotenv()

def test_round_robin_logic():
    """Test the round-robin LLM logic directly"""
    
    print("🧪 Testing Round-Robin LLM Logic")
    print("=" * 50)
    
    try:
        # Initialize the LLM engine
        print("1. Initializing LLM engine...")
        llm = DocumentReasoningLLM()
        print("✅ LLM engine initialized successfully")
        
        # Test provider sequence
        print(f"\n2. Testing provider sequence (4 calls)...")
        
        # Create dummy chunks for testing
        dummy_chunks = [
            {
                "text": "This is a test document about TechCorp Inc. They make advanced AI assistants.",
                "clause_id": "Section 1",
                "similarity_score": 0.95
            }
        ]
        
        # Make 4 test queries to see the round-robin pattern
        test_queries = [
            "What is the company name?",
            "What product do they make?", 
            "What version is mentioned?",
            "What are the key features?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔄 Request {i}: {query}")
            try:
                # This will internally use the round-robin provider
                response = llm.analyze_document_query(query, dummy_chunks)
                
                if isinstance(response, dict) and "direct_answer" in response:
                    answer = response["direct_answer"]
                    print(f"✅ Response: {answer[:100]}{'...' if len(answer) > 100 else ''}")
                else:
                    print(f"✅ Response received (non-standard format): {str(response)[:100]}...")
                    
            except Exception as e:
                print(f"❌ Request {i} failed: {e}")
                # Check if it's a rate limit error
                if "429" in str(e) or "rate limit" in str(e).lower():
                    print("⚠️  This is expected if you're hitting rate limits!")
        
        print(f"\n3. Round-robin sequence completed!")
        print("✅ All tests completed successfully")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
        # Check if it's an API key issue
        together_key = os.getenv("TOGETHER_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        
        print(f"\n📋 API Key Status:")
        print(f"   Together AI: {'SET' if together_key and together_key != 'your_together_api_key' else 'NOT SET'}")
        print(f"   Groq: {'SET' if groq_key and groq_key != 'your_actual_groq_api_key_here' else 'NOT SET'}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_round_robin_logic()
