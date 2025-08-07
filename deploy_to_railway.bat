@echo off
echo 🚀 Deploying Doc Chat fixes to Railway...
echo.

echo 📁 Adding all files...
git add .

echo 📝 Committing changes...
git commit -m "Fix embedding model timeout issue for Railway deployment

- Switch from intfloat/e5-large-v2 to sentence-transformers/all-MiniLM-L6-v2 
- Add fallback model loading with error handling
- Optimize startup process with better logging  
- Add Railway-specific configurations
- Disable reload mode for production
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
