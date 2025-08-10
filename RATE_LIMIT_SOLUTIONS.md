# Rate Limit Solutions Guide

You're encountering rate limit issues with your LLM provider. Here are multiple solutions to resolve this:

## 🚨 Current Issue Analysis
```
WARNING: Rate limit hit. Retrying in 1 seconds... (attempt 1/4)
WARNING: Rate limit hit. Retrying in 2 seconds... (attempt 2/4)
WARNING: Rate limit hit. Retrying in 4 seconds... (attempt 3/4)
ERROR: Max retries reached for rate limit. Failing.
```

This indicates your current API key has hit its rate limit. Here are the solutions:

## 🔧 Immediate Solutions

### Solution 1: Check Your API Key Status
```bash
# Check if you're using a placeholder key
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Current API key:', os.getenv('GROQ_API_KEY', 'not set')[:20] + '...' if os.getenv('GROQ_API_KEY') else 'NOT SET')"
```

### Solution 2: Get a Real Groq API Key
1. **Visit**: https://console.groq.com
2. **Sign Up/Login** 
3. **Navigate to**: API Keys section
4. **Create New Key** and copy it
5. **Update .env**:
   ```env
   GROQ_API_KEY=gsk_your_real_api_key_here
   ```

### Solution 3: Switch to Alternative Provider (Immediate Fix)
If Groq is rate limiting, switch providers in your `.env`:

**Option A: Together AI (Good Speed)**
```env
LLM_PROVIDER=together
TOGETHER_API_KEY=your_together_api_key
MODEL_NAME=meta-llama/Llama-2-7b-chat-hf
```

**Option B: Fireworks AI (Good Speed)**
```env
LLM_PROVIDER=fireworks
FIREWORKS_API_KEY=your_fireworks_api_key
MODEL_NAME=accounts/fireworks/models/llama-v2-7b-chat
```

## 🚀 Advanced Solutions

### Solution 4: Upgrade Your Groq Plan
- **Free Tier**: Limited requests per minute
- **Pro Tier**: Higher rate limits
- **Enterprise**: Unlimited requests

Visit https://console.groq.com/settings/billing

### Solution 5: Implement Request Spacing
Add delay between requests in your `.env`:
```env
REQUEST_DELAY=2  # Wait 2 seconds between requests
```

### Solution 6: Use Multiple API Keys (Load Balancing)
```env
# Primary
GROQ_API_KEY=your_primary_key

# Backup keys (system will rotate)
GROQ_API_KEY_2=your_backup_key_1
GROQ_API_KEY_3=your_backup_key_2
```

## 🔄 Updated Rate Limit Handling

I've already improved the rate limit handling in your system:
- ✅ Increased retries from 3 to 5 attempts
- ✅ Better exponential backoff (1s, 2s, 4s, 8s, 16s)
- ✅ Increased timeout from 15s to 20s
- ✅ Added fallback provider support

## 📊 Provider Comparison & Rate Limits

| Provider | Free Tier Limits | Speed | Quality | Cost |
|----------|------------------|-------|---------|------|
| **Groq** | 30 req/min | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Free |
| **Together AI** | 1 req/sec | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $0.20/M tokens |
| **Fireworks** | 10 req/min | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $0.20/M tokens |

## 🛠️ Quick Fix Commands

### Check Current Provider Status:
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

providers = {
    'groq': os.getenv('GROQ_API_KEY'),
    'together': os.getenv('TOGETHER_API_KEY'),
    'fireworks': os.getenv('FIREWORKS_API_KEY')
}

for name, key in providers.items():
    status = 'SET' if key and key != 'your_actual_groq_api_key_here' else 'NOT SET'
    print(f'{name.upper()}: {status}')
"
```

### Test Connection:
```bash
python -c "
from app.llm_utils import DocumentReasoningLLM
try:
    llm = DocumentReasoningLLM()
    print('✅ LLM initialized successfully!')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

## 🔐 Getting API Keys

### Groq (Recommended - Fastest)
1. Go to: https://console.groq.com
2. Sign up with email/GitHub
3. Navigate to "API Keys"
4. Click "Create API Key"
5. Copy the key (starts with `gsk_`)

### Together AI (Alternative)
1. Go to: https://api.together.xyz
2. Sign up and verify email
3. Go to "API Keys" in settings
4. Create new key
5. Copy the key

### Fireworks AI (Alternative)
1. Go to: https://fireworks.ai
2. Sign up for account
3. Navigate to API section
4. Generate API key
5. Copy the key

## ⚡ Emergency Fallback Solution

If you need immediate functionality without API keys, you can implement a mock response mode:

```env
# Emergency mode - uses local processing
LLM_PROVIDER=mock
ENABLE_MOCK_MODE=true
```

## 🔍 Monitoring & Prevention

### Set Rate Limit Monitoring:
```env
ENABLE_RATE_LIMIT_LOGGING=true
LOG_LEVEL=INFO
```

### Configure Request Throttling:
```env
MAX_REQUESTS_PER_MINUTE=25  # Stay under Groq's 30/min limit
REQUEST_TIMEOUT=30          # Increase timeout for busy periods
```

## 📞 Next Steps

1. **Immediate**: Update your `.env` with a real Groq API key
2. **Short-term**: Set up backup providers (Together AI or Fireworks)
3. **Long-term**: Consider upgrading to paid tiers for higher limits

## 🚨 Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Max retries reached" | Rate limit exceeded | Wait 1-2 minutes, then retry |
| "Invalid API key" | Wrong/expired key | Update with valid key |
| "Provider not found" | Typo in provider name | Check spelling in .env |
| "No API key" | Missing environment variable | Add API key to .env |

Your system now has improved rate limit handling and will be more resilient to these issues! 🎉
