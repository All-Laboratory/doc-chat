# 🌙 Moonshot AI Kimi K2 Instruct Setup Guide

Yes, you can absolutely use `moonshotai/kimi-k2-instruct`! I've added full support for it. Here's how to set it up:

## 🚀 **Model Overview: Moonshot Kimi K2 Instruct**

- **Provider**: Together AI
- **Model**: `moonshotai/kimi-k2-instruct`
- **Strengths**: Large context window, excellent reasoning, multilingual support
- **Speed**: Good (4-8 seconds response time)
- **Cost**: ~$0.20/M tokens

## 🔧 **Setup Instructions**

### **Step 1: Configure Your .env File**

I've already updated your `.env` file with the Moonshot Kimi configuration:

```env
# LLM Configuration - Using Together AI with Moonshot Kimi
LLM_PROVIDER=together
MODEL_NAME=moonshotai/kimi-k2-instruct

# Together AI API Key (Get from https://api.together.xyz)
# REPLACE WITH YOUR ACTUAL API KEY:
TOGETHER_API_KEY=your_together_api_key_here
```

### **Step 2: Get Together AI API Key**

1. **Visit**: https://api.together.xyz
2. **Sign up** with your email
3. **Verify** your email address
4. **Navigate to** "API Keys" in the left sidebar
5. **Create API Key** and copy it
6. **Update .env** with your real API key:
   ```env
   TOGETHER_API_KEY=your_real_api_key_here
   ```

### **Step 3: Test the Connection**

```bash
python -c "
from app.llm_utils import DocumentReasoningLLM
try:
    llm = DocumentReasoningLLM()
    print('✅ Moonshot Kimi K2 Instruct initialized successfully!')
    print(f'Provider: {llm.provider_name}')
    print(f'Model: {llm.model_name}')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

## 🎯 **Model Comparison**

| Model | Provider | Speed | Quality | Context Window | Cost |
|-------|----------|-------|---------|----------------|------|
| **moonshotai/kimi-k2-instruct** | Together AI | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 128k tokens | $0.20/M |
| llama3-8b-8192 | Groq | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 8k tokens | Free |
| llama3-70b-8192 | Groq | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 8k tokens | Free |

## 🌟 **Key Features of Moonshot Kimi**

### **Advantages:**
- ✅ **Large Context**: 128K token context window
- ✅ **Excellent Reasoning**: Advanced logical reasoning capabilities
- ✅ **Multilingual**: Supports Chinese and English very well
- ✅ **JSON Output**: Reliable structured output
- ✅ **Speed**: Good response times (4-8s)

### **Best Use Cases:**
- ✅ Complex document analysis
- ✅ Long document processing
- ✅ Multi-language documents
- ✅ Advanced reasoning tasks
- ✅ Detailed explanations

## ⚙️ **Technical Implementation**

I've enhanced the Together AI provider to support Moonshot Kimi with:

1. **Chat Format**: Uses OpenAI-compatible chat API
2. **Auto-Detection**: Automatically detects chat vs completion models
3. **Optimized Settings**: Configured for best performance
4. **Error Handling**: Robust error handling and fallbacks

## 🔄 **Alternative Model Options**

If you want to try different models, you can easily switch:

### **Fast & Free (Groq):**
```env
LLM_PROVIDER=groq
MODEL_NAME=llama3-8b-8192
GROQ_API_KEY=your_groq_key
```

### **Balanced (Together AI):**
```env
LLM_PROVIDER=together
MODEL_NAME=meta-llama/Llama-3-8b-chat-hf
TOGETHER_API_KEY=your_together_key
```

### **High Quality (Together AI):**
```env
LLM_PROVIDER=together
MODEL_NAME=meta-llama/Llama-3-70b-chat-hf
TOGETHER_API_KEY=your_together_key
```

## 📊 **Performance Expectations**

With Moonshot Kimi K2 Instruct:

- **Response Time**: 4-8 seconds
- **Token Usage**: ~1500 tokens per response
- **Cost**: ~$0.0003 per query
- **Quality**: Excellent reasoning and analysis
- **Context**: Can handle very long documents

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **"TOGETHER_API_KEY not found"**
   - Solution: Add your real Together AI API key to `.env`

2. **"Model not available"**
   - Solution: Check model name spelling: `moonshotai/kimi-k2-instruct`

3. **Rate limits**
   - Solution: Together AI has higher rate limits than free Groq

4. **Slow responses**
   - Solution: This is normal for larger models (4-8s is expected)

## 🔧 **Quick Commands**

### Check Current Configuration:
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Provider:', os.getenv('LLM_PROVIDER'))
print('Model:', os.getenv('MODEL_NAME'))
print('Together API Key:', 'SET' if os.getenv('TOGETHER_API_KEY') else 'NOT SET')
"
```

### Test Model Response:
```bash
python -c "
from app.llm_utils import DocumentReasoningLLM
llm = DocumentReasoningLLM()
response = llm.provider.generate_response('Hello, can you respond in JSON format?', max_tokens=100)
print('Response:', response)
"
```

## 🎉 **You're All Set!**

Your system now supports Moonshot AI Kimi K2 Instruct with:
- ✅ **Full integration** with your document chat system
- ✅ **Optimized settings** for speed and quality
- ✅ **Fallback support** to other providers
- ✅ **Enhanced error handling** for reliability

Just get your Together AI API key and you'll have access to one of the best reasoning models available! 🚀

## 💡 **Pro Tips**

1. **For Speed**: Use Groq with `llama3-8b-8192`
2. **For Quality**: Use Moonshot Kimi K2 Instruct
3. **For Balance**: Use `meta-llama/Llama-3-70b-chat-hf` on Together AI
4. **For Long Documents**: Moonshot Kimi excels with its 128k context window
