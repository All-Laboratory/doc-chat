@echo off
echo 🚀 Deploying Doc Chat fixes to Railway...
echo.

echo 🔧 Preparing Railway requirements...
python prepare_railway.py

echo 📁 Adding all files...
git add .

echo 📝 Committing changes...
git commit -m "Fix Railway deployment: embedding timeout + image size issues

🚀 EMBEDDING MODEL FIXES:
- Switch from intfloat/e5-large-v2 to sentence-transformers/all-MiniLM-L6-v2 
- Add fallback model loading with error handling
- Optimize startup process with better logging  

📦 IMAGE SIZE OPTIMIZATIONS:
- Switch to Nixpacks instead of Docker for better size optimization
- Add CPU-only PyTorch installation (saves ~2GB)
- Create ultra-minimal requirements.railway.txt
- Add Alpine Linux base with aggressive cleanup
- Add comprehensive .dockerignore file

⚙️ RAILWAY CONFIGURATIONS:
- Disable reload mode for production
- Add PORT environment variable support
- Optimized cache directories
- Add comprehensive deployment guide"

echo 📤 Pushing to GitHub...
git push origin main

echo.
echo ✅ Code pushed to GitHub!
echo.
echo 📋 Next steps:
echo 1. Go to your Railway dashboard
echo 2. Make sure these environment variables are set:
echo    - EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
echo    - PINECONE_API_KEY=your_actual_key
echo    - GROQ_API_KEY=your_actual_key
echo 3. Redeploy your application
echo 4. Monitor logs for successful startup
echo.
echo 🌐 Your app should now start without timeout issues!

pause
