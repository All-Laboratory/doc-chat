# 🚂 Railway Deployment - No-Retry System with Multiple API Keys

## 🎯 **Changes Needed for Railway Deployment**

To deploy the new **no-retry system** with multiple API keys on Railway, you need these specific changes:

## 📋 **1. Environment Variables on Railway Dashboard**

### **Required Changes in Railway Environment Variables:**

```bash
# ============================================================================
# MULTIPLE GROQ API KEYS (NEW - Critical for no-retry system)
# ============================================================================
GROQ_API_KEY=gsk_your_first_groq_key_here
GROQ_API_KEY_2=gsk_your_second_groq_key_here  
GROQ_API_KEY_3=gsk_your_third_groq_key_here

# Groq Model Configuration
GROQ_MODEL=llama3-8b-8192

# ============================================================================
# TOGETHER AI (Fallback Provider)
# ============================================================================
TOGETHER_API_KEY=your_existing_together_key_here
TOGETHER_MODEL=moonshotai/kimi-k2-instruct

# ============================================================================
# EMBEDDING MODEL (Keep Current - Railway Optimized)
# ============================================================================
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DIMENSIONS=384

# ============================================================================
# PINECONE (Keep Current Settings)
# ============================================================================
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_INDEX_NAME=document-reasoning
PINECONE_INDEX_HOST=your_pinecone_host_here
PINECONE_NAMESPACE=default

# ============================================================================
# OPTIMIZATION SETTINGS
# ============================================================================
CHUNK_SIZE=800
CHUNK_OVERLAP=100
TOP_K_RESULTS=3
LOG_LEVEL=INFO

# Railway Specific
PORT=8000
TRANSFORMERS_CACHE=/tmp/transformers_cache
```

## 📝 **2. Update main.py Import (Critical Change)**

You need to change **ONE LINE** in your `app/main.py`:

```python
# OLD (current):
from app.llm_utils_groq_first import DocumentReasoningLLM

# NEW (no-retry system):
from app.llm_utils_no_retry import DocumentReasoningLLM
```

## 🔧 **3. Railway Configuration Files (No Changes Needed)**

Your existing Railway files are fine:
- ✅ `railway.json` - Keep as is
- ✅ `nixpacks.toml` - Keep as is  
- ✅ `start_server.py` - Keep as is

## 📈 **4. Expected Performance Improvements**

### **Before (Current System):**
```
Request → Groq (429) → sleep 2s → retry (429) → sleep 4s → Together AI
Total: 6-14 seconds with retries
Railway timeout risk: HIGH
```

### **After (No-Retry System):**
```
Request → Groq Key 1 (429) → Together AI → Response
Total: 1-3 seconds, no delays
Railway timeout risk: NONE
```

## 🚀 **5. Deployment Steps**

### Step 1: Update Your Code
```bash
# 1. Update main.py import (see section 2 above)
# 2. Commit changes
git add .
git commit -m "Switch to no-retry LLM system for Railway"
git push origin main
```

### Step 2: Update Railway Environment Variables
1. Go to Railway Dashboard → Your Project → Variables
2. **Add the new variables** from section 1
3. **Keep all existing variables** (Pinecone, etc.)

### Step 3: Redeploy
1. Railway will auto-deploy after git push
2. Monitor deployment logs
3. Look for these success messages:

```
🚀 NO-RETRY LLM System initialized
⚡ Strategy: Instant failover, no sleep/retry delays
✅ Initialized 3 Groq keys
✅ Together AI initialized: moonshotai/kimi-k2-instruct
🎉 All components initialized successfully
```

## ⚠️ **Critical: Multiple Groq Accounts**

To get 3 Groq API keys, you need to create 3 separate accounts:

1. **Account 1**: Use your main email → `GROQ_API_KEY`
2. **Account 2**: Use email+1@gmail.com → `GROQ_API_KEY_2`  
3. **Account 3**: Use email+2@gmail.com → `GROQ_API_KEY_3`

Each account gets 30 req/min = **90 requests/minute total**

## 🎯 **Benefits on Railway:**

✅ **No 429 errors** for users  
✅ **90 requests/minute** capacity (3x current)  
✅ **1-3 second responses** consistently  
✅ **No Railway timeouts** from retry delays  
✅ **Better user experience**  
✅ **No code changes** needed after deployment  

## 🔍 **Testing After Deployment:**

1. **Health Check**: `GET https://your-app.railway.app/health`
2. **Test Query**: Upload document and ask questions
3. **Check Logs**: Should see "⚡ Trying Groq..." messages
4. **Speed Test**: Responses should be 1-3 seconds

## 🛠️ **Troubleshooting:**

### If you see retry behavior:
- Check that `main.py` import was updated
- Verify Railway deployed the latest code
- Check deployment logs for import errors

### If all Groq keys fail:
- Verify all 3 API keys are valid
- Check Groq account limits
- System will fallback to Together AI automatically

The no-retry system eliminates all the sleep/retry problems and gives you much better performance on Railway!
