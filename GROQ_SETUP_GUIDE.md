# 🚀 GROQ SETUP GUIDE - Get Ultra-Fast Responses

## Step 1: Create New Groq Account
1. Go to: https://console.groq.com
2. Click "Sign Up" (use new email if you had issues before)
3. Verify your email
4. Login to Groq Console

## Step 2: Generate API Key
1. In Groq Console, go to "API Keys"
2. Click "Create API Key"
3. Name it: "document-chat-project"
4. Copy the key (starts with `gsk_...`)

## Step 3: Update Your .env File
Replace this line in your .env:
```bash
# OLD (slow)
GROQ_API_KEY=your_actual_groq_api_key_here

# NEW (fast)
GROQ_API_KEY=gsk_your_actual_new_key_here
```

## Step 4: Test the Speed
Run your application and try a query - you should see:
- Response time: 1-3 seconds (instead of 8-15s)
- Logs showing: "🚀 Trying Groq..."
- Much faster document reasoning

## Expected Results:
✅ Ultra-fast responses (1-2 seconds)
✅ 30 requests/minute free tier
✅ Automatic fallback to Together AI if needed
✅ Much better user experience

## Rate Limits (Free Tier):
- 30 requests per minute
- 14,400 tokens per minute  
- Perfect for development and testing

## Troubleshooting:
If you still get slow responses:
1. Check logs for "🚀 Trying Groq..." message
2. Verify API key starts with "gsk_"
3. Make sure GROQ_MODEL=llama3-8b-8192 (not 70b)
4. Restart your application after changing .env
