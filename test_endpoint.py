# Add this endpoint to your main.py to test keys on Railway

@app.get("/test-groq-keys")
async def test_groq_keys():
    """Test endpoint to check which Groq keys are working on Railway"""
    import requests
    
    results = {}
    
    keys_to_test = [
        ("GROQ_API_KEY", os.getenv("GROQ_API_KEY")),
        ("GROQ_API_KEY_2", os.getenv("GROQ_API_KEY_2")),
        ("GROQ_API_KEY_3", os.getenv("GROQ_API_KEY_3"))
    ]
    
    working_count = 0
    
    for key_name, api_key in keys_to_test:
        if not api_key:
            results[key_name] = "NOT SET"
            continue
            
        if not api_key.startswith("gsk_"):
            results[key_name] = "INVALID FORMAT"
            continue
        
        # Test the key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 5
        }
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                results[key_name] = "WORKING ✅"
                working_count += 1
            elif response.status_code == 401:
                results[key_name] = "INVALID KEY ❌"
            elif response.status_code == 429:
                results[key_name] = "RATE LIMITED ⚠️ (but valid)"
                working_count += 1
            else:
                results[key_name] = f"ERROR {response.status_code}"
                
        except Exception as e:
            results[key_name] = f"CONNECTION ERROR: {str(e)}"
    
    return {
        "working_keys": f"{working_count}/3",
        "results": results,
        "recommendation": "Fix invalid keys in Railway environment variables" if working_count < 3 else "All keys working!"
    }
