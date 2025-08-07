# Railway Deployment Guide - Doc Chat Application

This guide will help you deploy the doc-chat application on Railway successfully, fixing the embedding model timeout issue.

## Problem Fixed

The application was getting stuck at:
```
INFO:sentence_transformers.SentenceTransformer:Load pretrained SentenceTransformer: intfloat/e5-large-v2
```

**Root Cause**: The `intfloat/e5-large-v2` model is very large (~1.3GB) and takes too long to download and initialize on Railway, causing deployment timeouts.

## Solution

1. **Changed to smaller, faster embedding model**: `sentence-transformers/all-MiniLM-L6-v2` (only ~90MB)
2. **Added fallback model loading** with error handling
3. **Optimized startup process** with better logging
4. **Fixed Railway-specific configuration**

## Deployment Steps

### 1. Environment Variables

Set these environment variables in your Railway dashboard:

```bash
# Essential - Replace with your actual keys
PINECONE_API_KEY=your_actual_pinecone_api_key
GROQ_API_KEY=your_actual_groq_api_key

# Embedding Model - IMPORTANT: Use smaller model for Railway
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Pinecone Configuration
PINECONE_INDEX_NAME=document-reasoning
PINECONE_NAMESPACE=default

# Other configurations (adjust as needed)
LLM_PROVIDER=groq
MODEL_NAME=llama3-70b-8192
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=5

# Railway optimizations
TRANSFORMERS_CACHE=/tmp/transformers_cache
PORT=8000
```

### 2. Push Changes to GitHub

Make sure your GitHub repository has all the latest changes:

```bash
git add .
git commit -m "Fix embedding model timeout for Railway deployment"
git push origin main
```

### 3. Deploy on Railway

1. Go to your Railway dashboard
2. Redeploy your application
3. Monitor the build logs - you should now see:
   ```
   🚀 Starting Document Reasoning Assistant...
   📄 Initializing Document Extractor...
   ✅ Document Extractor initialized
   🧠 Initializing Cloud Document Retriever (Embedding Model + Pinecone)...
   📥 This may take a moment to download the embedding model...
   ✅ Model loaded successfully: sentence-transformers/all-MiniLM-L6-v2 (dimension: 384)
   ✅ Cloud Document Retriever initialized successfully
   🤖 Initializing LLM Engine...
   ✅ LLM Engine initialized
   🎉 All components initialized successfully
   🌐 Application is ready to serve requests!
   ```

### 4. Test Your Deployment

Once deployed, test the endpoints:

1. **Health Check**: `GET https://your-app-url.railway.app/health`
2. **API Documentation**: `https://your-app-url.railway.app/docs`
3. **Main Endpoint**: `POST https://your-app-url.railway.app/hackrx/run`

## Key Changes Made

### 1. Embedding Model Optimization
- **Before**: `intfloat/e5-large-v2` (1.3GB, 1024 dimensions)
- **After**: `sentence-transformers/all-MiniLM-L6-v2` (90MB, 384 dimensions)

### 2. Fallback Model Loading
```python
fallback_models = [
    self.embedding_model_name,
    "sentence-transformers/all-MiniLM-L6-v2",  # Small and fast
    "sentence-transformers/paraphrase-MiniLM-L6-v2"  # Alternative
]
```

### 3. Better Error Handling
- Added comprehensive logging with emojis for better visibility
- Added model loading timeout handling
- Added fallback mechanisms

### 4. Railway-Specific Optimizations
- Disabled reload mode in production
- Set single worker configuration
- Added PORT environment variable support
- Optimized cache directory

## Troubleshooting

### If deployment still times out:
1. Check Railway logs for specific error messages
2. Ensure all environment variables are set correctly
3. Try redeploying from scratch

### If Pinecone connection fails:
1. Verify PINECONE_API_KEY is correct
2. Check Pinecone index configuration
3. Ensure index dimensions match the model (384 for all-MiniLM-L6-v2)

### If model performance is lower:
The smaller model has slightly lower accuracy but is much faster and suitable for Railway deployment. If you need higher accuracy, consider:
1. Using a more powerful cloud provider with longer timeout limits
2. Pre-downloading and caching models
3. Using model quantization techniques

## Performance Comparison

| Model | Size | Dimensions | Download Time | Accuracy |
|-------|------|------------|---------------|----------|
| `intfloat/e5-large-v2` | ~1.3GB | 1024 | ~5-10 min | High |
| `all-MiniLM-L6-v2` | ~90MB | 384 | ~30-60 sec | Good |

The smaller model provides adequate performance for most document reasoning tasks while ensuring reliable deployment on Railway.
