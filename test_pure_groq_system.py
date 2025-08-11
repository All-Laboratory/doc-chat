#!/usr/bin/env python3
"""
Test the Pure 4-Groq System
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv('.env')

# Add app to path
sys.path.append('app')

try:
    from llm_utils_groq_first import DocumentReasoningLLM
    
    print("🚀 Testing Pure 4-Groq System...")
    print("=" * 60)
    
    # Check API keys
    print("📋 Groq API Key Status:")
    groq_keys = []
    for i in range(1, 5):
        key_name = f"GROQ_API_KEY_{i}" if i > 1 else "GROQ_API_KEY"
        key = os.getenv(key_name)
        if key and key not in ["your_first_groq_api_key_here", "your_second_groq_api_key_here", "your_third_groq_api_key_here", "your_fourth_groq_api_key_here", "your_actual_groq_api_key_here", "your_groq_api_key"]:
            groq_keys.append(i)
            model_name = f"GROQ_MODEL_{i}" if i > 1 else "GROQ_MODEL_1"
            model = os.getenv(model_name, "default")
            print(f"   ✅ Groq Key {i}: Set ({model})")
        else:
            model_name = f"GROQ_MODEL_{i}" if i > 1 else "GROQ_MODEL_1"
            model = os.getenv(model_name, "default")
            print(f"   ❌ Groq Key {i}: Not set (placeholder) - would use {model}")
    
    print(f"\n📊 Summary: {len(groq_keys)}/4 Groq keys configured")
    if groq_keys:
        print(f"⚡ Available capacity: {len(groq_keys) * 30} requests/minute")
    print()
    
    # Initialize LLM
    print("🤖 Initializing Pure Groq System...")
    try:
        llm = DocumentReasoningLLM()
        print("✅ System initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        sys.exit(1)
    
    print()
    
    # Test with sample document chunks
    test_chunks = [
        {
            "text": "The insurance policy covers accidental injuries including paralysis caused by accidents. Coverage is effective immediately after policy activation. Maximum benefit: $100,000 for paralysis claims.",
            "clause_id": "Section 3.1 - Coverage Details",
            "similarity_score": 0.95,
            "chunk_id": "chunk_1"
        },
        {
            "text": "Exclusions: Pre-existing conditions are not covered. Injuries caused by self-inflicted harm, substance abuse, or criminal activities are excluded from coverage.",
            "clause_id": "Section 5.2 - Exclusions", 
            "similarity_score": 0.87,
            "chunk_id": "chunk_2"
        },
        {
            "text": "Claims process: Submit within 30 days of incident. Medical documentation from licensed physician required. Processing time: 5-10 business days.",
            "clause_id": "Section 7.1 - Claims Process",
            "similarity_score": 0.82,
            "chunk_id": "chunk_3"
        }
    ]
    
    test_query = "Does the policy cover paralysis from accidents and what's the maximum benefit?"
    
    print(f"❓ Test Query: {test_query}")
    print("📊 Testing with sample document chunks...")
    print()
    
    # Test the system
    try:
        response = llm.analyze_document_query(test_query, test_chunks)
        
        print("✅ Response Generated Successfully!")
        print("=" * 60)
        print(f"📋 Decision: {response.get('decision', 'Unknown')}")
        print(f"💬 Direct Answer: {response.get('direct_answer', 'No answer')}")
        print(f"📝 Justification: {response.get('justification', 'No justification')[:200]}...")
        
        referenced_clauses = response.get('referenced_clauses', [])
        print(f"📚 Referenced Clauses: {len(referenced_clauses)}")
        
        for i, clause in enumerate(referenced_clauses[:2], 1):
            print(f"   {i}. {clause.get('clause_id', 'Unknown')}")
            print(f"      Text: {clause.get('text', '')[:100]}...")
            print(f"      Reason: {clause.get('reasoning', '')[:100]}...")
        
        print()
        
    except Exception as e:
        print(f"❌ Error during query processing: {e}")
        print(f"📋 Error type: {type(e).__name__}")
    
    # Test provider status
    print("📊 Provider Status Report:")
    print("-" * 50)
    try:
        status = llm.get_provider_status()
        
        groq_available = 0
        groq_total = 0
        
        for key, provider_info in status.items():
            if key.startswith('groq_'):
                groq_total += 1
                if provider_info.get('available'):
                    groq_available += 1
                    status_icon = "✅"
                    status_text = "Available"
                elif provider_info.get('model') == 'Not configured':
                    status_icon = "⚪"
                    status_text = "Not Configured"
                elif provider_info.get('rate_limited'):
                    status_icon = "🚦"
                    status_text = "Rate Limited"
                else:
                    status_icon = "❌"
                    status_text = "Unavailable"
                
                model = provider_info.get('model', 'Unknown')
                print(f"   {status_icon} {key.upper()}: {status_text} ({model})")
        
        print()
        print(f"📈 Summary: {groq_available}/{groq_total} Groq providers available")
        
        if groq_available > 0:
            total_groq_capacity = groq_available * 30
            print(f"⚡ Available Groq capacity: {total_groq_capacity} requests/minute")
        
    except Exception as e:
        print(f"   ❌ Error getting provider status: {e}")
    
    print()
    print("🎉 Pure 4-Groq System Test Complete!")
    print("=" * 60)
    
    # Recommendations
    print("📋 System Configuration:")
    print(f"   🔑 Groq Keys Configured: {len(groq_keys)}/4")
    print("   🚫 Together AI: Removed (Pure Groq system)")
    print("   🎯 Strategy: Round-robin through all Groq providers")
    print("   ⚡ Maximum Capacity: 120 requests/minute (4 × 30)")
    print("   🔄 Fallback: Intelligent rate limit handling")
    
    if len(groq_keys) < 4:
        print(f"\n💡 Recommendation: Add {4 - len(groq_keys)} more Groq API keys for maximum capacity")
        print("   Get free keys at: https://console.groq.com")
    else:
        print("\n✅ Optimal Configuration: All 4 Groq keys ready!")
        
except Exception as e:
    print(f"❌ Error testing Pure Groq system: {str(e)}")
    print(f"📋 Error type: {type(e).__name__}")
    import traceback
    print(f"📋 Traceback: {traceback.format_exc()}")
