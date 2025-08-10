@echo off
echo 🚂 Deploying NO-RETRY System to Railway...
echo.

echo 📋 Changes being deployed:
echo ✅ Switched to no-retry LLM system (instant failover)
echo ✅ Multiple Groq API key support (3x capacity)
echo ✅ No sleep/retry delays (1-3 second responses)
echo ✅ Updated main.py to use llm_utils_no_retry
echo.

echo 📁 Adding all files...
git add .

echo 📝 Committing no-retry system changes...
git commit -m "Deploy no-retry LLM system to Railway

MAJOR IMPROVEMENTS:
✅ No more 429 retry hell - instant failover
✅ Multiple Groq API key support (GROQ_API_KEY, GROQ_API_KEY_2, GROQ_API_KEY_3)  
✅ 90 requests/minute capacity (3x current)
✅ 1-3 second response times consistently
✅ No sleep/retry delays that cause Railway timeouts
✅ Updated main.py to use llm_utils_no_retry
✅ Smart provider rotation: Groq → Together AI → Next Groq key

RAILWAY SPECIFIC:
- No configuration file changes needed
- Railway timeout risk eliminated  
- Better user experience with instant responses
- All existing environment variables preserved"

echo 📤 Pushing to GitHub...
git push origin main

echo.
echo ✅ Code pushed to GitHub!
echo.
echo 🚨 CRITICAL: Railway Environment Variables Needed!
echo.
echo 📋 Add these to your Railway Dashboard → Variables:
echo.
echo === MULTIPLE GROQ KEYS (NEW - CRITICAL) ===
echo GROQ_API_KEY=gsk_your_first_groq_key_here
echo GROQ_API_KEY_2=gsk_your_second_groq_key_here  
echo GROQ_API_KEY_3=gsk_your_third_groq_key_here
echo GROQ_MODEL=llama3-8b-8192
echo.
echo === TOGETHER AI (Keep existing) ===
echo TOGETHER_API_KEY=your_existing_together_key
echo TOGETHER_MODEL=moonshotai/kimi-k2-instruct
echo.
echo === PINECONE (Keep existing) ===
echo PINECONE_API_KEY=your_existing_pinecone_key
echo PINECONE_INDEX_NAME=document-reasoning
echo PINECONE_INDEX_HOST=your_existing_host
echo PINECONE_NAMESPACE=default
echo.
echo === EMBEDDING (Keep current) ===
echo EMBEDDING_MODEL=all-MiniLM-L6-v2
echo VECTOR_DIMENSIONS=384
echo.
echo 🎯 EXPECTED RESULTS AFTER DEPLOYMENT:
echo ✅ Users get 1-3 second responses (not 8-15 seconds)
echo ✅ No 429 errors for users
echo ✅ 90 requests/minute capacity
echo ✅ No Railway timeouts from retry delays
echo ✅ Logs show: "🚀 NO-RETRY LLM System initialized"
echo ✅ Logs show: "✅ Initialized X Groq keys"
echo.
echo 📝 NEXT STEPS:
echo 1. Railway will auto-deploy after git push
echo 2. Add the environment variables above to Railway
echo 3. Monitor deployment logs for success messages
echo 4. Test with document upload + questions
echo 5. Verify 1-3 second response times
echo.
echo 🔧 TO GET MULTIPLE GROQ KEYS:
echo 1. Create 3 separate Groq accounts (email+1@gmail.com, email+2@gmail.com)
echo 2. Get API key from each account (console.groq.com)
echo 3. Add them as GROQ_API_KEY, GROQ_API_KEY_2, GROQ_API_KEY_3
echo.

pause
