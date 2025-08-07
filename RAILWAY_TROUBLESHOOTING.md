# Railway Deployment Troubleshooting Guide

## Common Build Errors and Solutions

### ❌ Error: "pip install process did not complete successfully: exit code: 1"

**Cause**: Package installation conflicts or dependency resolution issues

**Solutions**:

1. **Check build logs** for specific package that failed
2. **Use Nixpacks instead of Docker**:
   - Remove or rename `Dockerfile` to `Dockerfile.backup`
   - Railway will automatically use Nixpacks

3. **Verify requirements.txt**:
   ```bash
   # Make sure you're using the Railway-optimized requirements
   python prepare_railway.py
   ```

### ❌ Error: "image exceeded the size"

**Cause**: Docker image is too large for Railway's limits

**Solutions**:

1. **Remove Docker completely**:
   ```bash
   mv Dockerfile Dockerfile.backup
   ```

2. **Use Nixpacks with optimized configuration**:
   - Railway automatically detects Python and uses Nixpacks
   - Much smaller final image size
   - Better caching and optimization

3. **Verify minimal requirements**:
   - Using `requirements.railway.txt` with only essential packages
   - CPU-only PyTorch installation
   - No CUDA dependencies

### ❌ Error: PyTorch installation timeout

**Cause**: Trying to install full PyTorch with CUDA support

**Solutions**:

1. **Force CPU-only installation**:
   ```bash
   # Set environment variable in Railway dashboard
   TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
   ```

2. **Use our Nixpacks configuration**:
   - `nixpacks.toml` handles PyTorch installation correctly
   - Installs CPU-only version explicitly

### ❌ Error: sentence-transformers installation fails

**Cause**: PyTorch not installed first or wrong version

**Solutions**:

1. **Install in correct order** (handled by Nixpacks):
   - PyTorch CPU-only first
   - Then sentence-transformers
   - This is automated in our `nixpacks.toml`

2. **Use fallback model**:
   ```bash
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```

### ❌ Error: "No module named 'app.main'"

**Cause**: Import path issues or missing files

**Solutions**:

1. **Check file structure**:
   ```
   /
   ├── app/
   │   ├── __init__.py
   │   ├── main.py
   │   └── ...
   ├── start_server.py
   └── requirements.txt
   ```

2. **Verify start command**:
   ```bash
   # In railway.json
   "startCommand": "python start_server.py"
   ```

## Build Optimization Checklist

### ✅ Pre-deployment Checklist

- [ ] Run `python prepare_railway.py` to set up requirements
- [ ] Ensure `Dockerfile` is removed/renamed (use Nixpacks instead)
- [ ] Verify `nixpacks.toml` configuration exists
- [ ] Check `railway.json` uses Nixpacks builder
- [ ] Set essential environment variables in Railway dashboard

### ✅ Environment Variables (Railway Dashboard)

**Essential:**
```bash
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
PINECONE_API_KEY=your_actual_key
GROQ_API_KEY=your_actual_key
```

**Optimization:**
```bash
TRANSFORMERS_CACHE=/tmp/transformers_cache
HF_HOME=/tmp/huggingface_cache
TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
PIP_NO_CACHE_DIR=1
```

### ✅ File Structure Verification

Required files:
- `app/main.py` ✅
- `start_server.py` ✅
- `requirements.txt` (generated from requirements.railway.txt) ✅
- `nixpacks.toml` ✅
- `railway.json` ✅

Optional but recommended:
- `.dockerignore` (to exclude unnecessary files)
- `requirements.railway.txt` (minimal requirements)

## Advanced Troubleshooting

### Debug Build Process

1. **Check Railway build logs**:
   - Look for the specific package that fails
   - Note the exact error message
   - Check memory usage during build

2. **Test locally with Nixpacks**:
   ```bash
   # If you have Nixpacks installed locally
   nixpacks build . --name test-app
   ```

3. **Minimal test deployment**:
   ```bash
   # Create a minimal app with just FastAPI
   # Deploy to test basic functionality
   # Add dependencies one by one
   ```

### Memory Optimization

If build fails due to memory limits:

1. **Reduce concurrent installations**:
   - Nixpacks handles this automatically
   - Installs packages in smaller batches

2. **Use lighter alternatives**:
   - `python-docx` instead of `python-docx2txt`
   - `pymupdf` instead of `PyPDF2`
   - CPU-only PyTorch

3. **Enable build optimizations**:
   ```bash
   # In Railway dashboard
   PIP_NO_CACHE_DIR=1
   PYTHONUNBUFFERED=1
   ```

## Success Indicators

### ✅ Successful Build Logs Should Show:

```
Setting up Railway-optimized Python environment...
Installing core dependencies...
Installing PyTorch CPU-only...
Installing ML and document processing...
Installing database and API clients...
Optimizing installation...
Build optimization complete
```

### ✅ Successful Runtime Logs Should Show:

```
🚀 Starting Document Reasoning Assistant...
📄 Initializing Document Extractor...
✅ Document Extractor initialized
🧠 Initializing Cloud Document Retriever (Embedding Model + Pinecone)...
✅ Model loaded successfully: sentence-transformers/all-MiniLM-L6-v2 (dimension: 384)
✅ Cloud Document Retriever initialized successfully
🤖 Initializing LLM Engine...
✅ LLM Engine initialized
🎉 All components initialized successfully
🌐 Application is ready to serve requests!
```

## Contact Points

If issues persist after following this guide:

1. **Check Railway status**: https://status.railway.app/
2. **Review Railway docs**: https://docs.railway.app/
3. **Check build environment**: Ensure Railway has enough resources
4. **Test with minimal configuration**: Start with basic FastAPI app

Remember: The key is using **Nixpacks instead of Docker** for Railway deployments!
