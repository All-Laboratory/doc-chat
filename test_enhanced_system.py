#!/usr/bin/env python3
"""
Test the Enhanced Fallback LLM System
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv('.env')

# Add app to path
sys.path.append('app')

try:
    from llm_utils_enhanced_fallback import DocumentReasoningLLM
    
    print("🚀 Testing Enhanced Fallback LLM System...")
    print(f"📝 Together API Key: {'✅ Set' if os.getenv('TOGETHER_API_KEY') and os.getenv('TOGETHER_API_KEY') not in ['your_together_api_key', 'your_actual_api_key'] else '❌ Not set'}")
    print(f"📝 Groq API Key: {'✅ Set' if os.getenv('GROQ_API_KEY') and os.getenv('GROQ_API_KEY') not in ['your_actual_groq_api_key_here', 'your_groq_api_key'] else '❌ Not set (fallback)'}")
    
    # Initialize LLM
    print("\n🤖 Initializing LLM engine...")
    llm = DocumentReasoningLLM()
    
    # Test with sample document chunks
    test_chunks = [
        {
            "text": "The policy covers accidental injuries including paralysis caused by accidents. Coverage is effective immediately after policy activation. The maximum benefit is $100,000 for paralysis claims.",
            "clause_id": "Section 3.1",
            "similarity_score": 0.95,
            "chunk_id": "chunk_1"
        },
        {
            "text": "Exclusions: Pre-existing conditions are not covered. Injuries caused by self-inflicted harm, substance abuse, or criminal activities are excluded.",
            "clause_id": "Section 5.2", 
            "similarity_score": 0.87,
            "chunk_id": "chunk_2"
        }
    ]
    
    test_query = "Does the policy cover paralysis?"
    
    print(f"\n❓ Test Query: {test_query}")
    print("📊 Testing with sample document chunks...")
    
    # Test the system
    response = llm.analyze_document_query(test_query, test_chunks)
    
    print("\n✅ Response Generated Successfully!")
    print(f"📋 Decision: {response.get('decision', 'Unknown')}")
    print(f"💬 Direct Answer: {response.get('direct_answer', 'No answer')[:100]}...")
    print(f"📚 Referenced Clauses: {len(response.get('referenced_clauses', []))}")
    
    # Test provider status
    print("\n📊 Provider Status:")
    try:
        status = llm.get_provider_status()
        for provider_name, provider_info in status.items():
            available = "✅ Available" if provider_info.get('available') else "❌ Not Available"
            model = provider_info.get('model', 'Unknown')
            print(f"   {provider_name}: {available} ({model})")
    except Exception as e:
        print(f"   Error getting provider status: {e}")
    
    print("\n🎉 Enhanced Fallback System Test Complete!")
    print("✅ The system is working properly and should provide better error handling.")
    
except Exception as e:
    print(f"❌ Error testing enhanced fallback system: {str(e)}")
    print(f"📋 Error type: {type(e).__name__}")
    import traceback
    print(f"📋 Full traceback: {traceback.format_exc()}")
