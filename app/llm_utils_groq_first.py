import os
import json
import logging
import requests
import time
import random
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider:
    """Base class for LLM providers with rate limit tracking"""
    
    def __init__(self, api_key: str, model_name: str, provider_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self.provider_name = provider_name
        self.last_rate_limit_time = None
        self.consecutive_failures = 0
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError
    
    def is_rate_limited(self) -> bool:
        """Check if this provider is currently rate limited (60 second cooldown)"""
        if self.last_rate_limit_time is None:
            return False
        
        time_since_rate_limit = time.time() - self.last_rate_limit_time
        return time_since_rate_limit < 60
    
    def mark_rate_limited(self):
        """Mark this provider as rate limited"""
        self.last_rate_limit_time = time.time()
        self.consecutive_failures += 1
        logger.warning(f"🚦 {self.provider_name} hit rate limit. Cooling down for 60 seconds...")
    
    def mark_success(self):
        """Reset failure counter on successful request"""
        self.consecutive_failures = 0

class GroqProvider(LLMProvider):
    """Groq provider - Fast and reliable"""
    
    def __init__(self, api_key: str, model_name: str = "llama3-8b-8192", provider_name: str = "Groq"):
        super().__init__(api_key, model_name, provider_name)
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def generate_response(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
            
            # Check for rate limiting
            if response.status_code == 429:
                self.mark_rate_limited()
                raise requests.exceptions.RequestException(f"Rate limit exceeded (429) for {self.provider_name}")
            
            response.raise_for_status()
            result = response.json()
            
            # Mark success
            self.mark_success()
            
            return result["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            # Check if it's a rate limit error
            if "429" in error_msg or "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                self.mark_rate_limited()
            logger.error(f"Groq API request failed: {error_msg}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected Groq response format: {str(e)}")
            raise

class TogetherAIProvider(LLMProvider):
    """Together AI provider - Powerful models"""
    
    def __init__(self, api_key: str, model_name: str):
        super().__init__(api_key, model_name, "Together AI")
        # Support both old inference and new chat endpoints
        if any(model in model_name.lower() for model in ["kimi", "llama-3", "deepseek-r1", "deepseek"]):
            self.base_url = "https://api.together.xyz/v1/chat/completions"
            self.is_chat_model = True
        else:
            self.base_url = "https://api.together.xyz/inference"
            self.is_chat_model = False
    
    def generate_response(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if self.is_chat_model:
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9
            }
        else:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "stop": ["<|im_end|>", "<|endoftext|>"]
            }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
            
            # Check for rate limiting
            if response.status_code == 429:
                self.mark_rate_limited()
                raise requests.exceptions.RequestException(f"Rate limit exceeded (429) for {self.provider_name}")
            
            response.raise_for_status()
            result = response.json()
            
            # Mark success
            self.mark_success()
            
            if self.is_chat_model:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return result["output"]["choices"][0]["text"].strip()
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            # Check if it's a rate limit error
            if "429" in error_msg or "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                self.mark_rate_limited()
            logger.error(f"Together AI API request failed: {error_msg}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected Together AI response format: {str(e)}")
            raise

class DocumentReasoningLLM:
    """Groq-First System: 3 Groq models as primary providers, Together AI as backup"""
    
    def __init__(self):
        self.groq_providers = self._initialize_groq_providers()
        self.together_provider = self._initialize_together()
        
        if not self.groq_providers and not self.together_provider:
            raise ValueError("At least one API key (GROQ_API_KEY or TOGETHER_API_KEY) must be set")
        
        # Log what we have available
        available_providers = []
        if self.groq_providers:
            available_providers.extend([f"Groq-{i+1}" for i in range(len(self.groq_providers))])
        if self.together_provider:
            available_providers.append("Together AI")
        
        logger.info(f"🚀 Groq-First System Initialized with providers: {' → '.join(available_providers)}")
        logger.info(f"📋 Strategy: Try all {len(self.groq_providers)} Groq models first, then Together AI backup")
        logger.info(f"⚡ Total Groq capacity: {len(self.groq_providers) * 30} requests/minute")
        
        # Railway environment optimization
        railway_env = os.getenv("RAILWAY_ENVIRONMENT")
        if railway_env:
            logger.info(f"🚂 Running on Railway environment: {railway_env}")
    
    def _initialize_groq_providers(self) -> List[GroqProvider]:
        """Initialize multiple Groq providers"""
        providers = []
        
        # Try to get multiple Groq API keys
        for i in range(1, 4):  # Support up to 3 Groq keys
            key_name = f"GROQ_API_KEY_{i}" if i > 1 else "GROQ_API_KEY"
            key = os.getenv(key_name)
            
            if key and key not in ["your_actual_groq_api_key_here", "your_groq_api_key"]:
                # Use different models for variety if available
                if i == 1:
                    model = os.getenv("GROQ_MODEL_1", os.getenv("GROQ_MODEL", "llama3-8b-8192"))
                elif i == 2:
                    model = os.getenv("GROQ_MODEL_2", "llama3-70b-8192")
                else:
                    model = os.getenv("GROQ_MODEL_3", "mixtral-8x7b-32768")
                
                try:
                    provider = GroqProvider(key, model, f"Groq-{i}")
                    providers.append(provider)
                    logger.info(f"✅ Groq provider {i} initialized with model: {model}")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize Groq provider {i}: {e}")
        
        if not providers:
            logger.warning("⚠️ No valid Groq API keys found. Set GROQ_API_KEY, GROQ_API_KEY_2, GROQ_API_KEY_3")
        
        return providers
    
    def _initialize_together(self) -> Optional[TogetherAIProvider]:
        """Initialize Together AI provider as backup"""
        together_key = os.getenv("TOGETHER_API_KEY")
        if together_key and together_key not in ["your_together_api_key", "your_actual_api_key"]:
            model = os.getenv("TOGETHER_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Llama-70B")
            try:
                provider = TogetherAIProvider(together_key, model)
                logger.info(f"✅ Together AI backup provider initialized with model: {model}")
                return provider
            except Exception as e:
                logger.error(f"❌ Failed to initialize Together AI: {e}")
                return None
        else:
            logger.warning("⚠️ Together AI API key not found or invalid (backup only)")
            return None
    
    def create_reasoning_prompt(self, query: str, relevant_chunks: List[Dict]) -> str:
        """Create a structured prompt for document reasoning"""
        
        # Format relevant chunks
        context_sections = []
        for i, chunk in enumerate(relevant_chunks[:5], 1):  # Limit to top 5
            clause_id = chunk.get("clause_id", f"Section {i}")
            text = chunk["text"][:1000]  # Truncate if too long
            
            context_sections.append(f"""### {clause_id}
{text}
""")
        
        context = "\n".join(context_sections)
        
        prompt = f"""You are an expert document analysis assistant. Your task is to analyze documents and provide direct, concise responses to user queries.

## CONTEXT FROM DOCUMENT:
{context}

## USER QUERY:
{query}

## INSTRUCTIONS:
Analyze the provided document sections and answer the user's query. You must respond with a valid JSON object in exactly this format:

{{
  "direct_answer": "A concise, direct answer to the user's question (e.g., 'Yes, according to the document the policy covers paralysis' or 'No, the scheme does not cover this condition')",
  "decision": "Approved" | "Denied" | "Uncertain",
  "justification": "Clear reasoning based on the document analysis",
  "referenced_clauses": [
    {{
      "clause_id": "section identifier from document",
      "text": "relevant excerpt from the clause",
      "reasoning": "why this clause is relevant to the decision"
    }}
  ],
  "additional_info": "Any additional relevant information, context, or conditions that the user should know about"
}}

## DECISION CRITERIA:
- **Approved**: The document clearly supports the user's request/claim
- **Denied**: The document explicitly prohibits or excludes the request/claim
- **Uncertain**: The document is ambiguous, lacks specific coverage details, or requires additional information

## REQUIREMENTS:
1. The direct_answer should be conversational and directly address the user's question
2. Base your decision ONLY on the provided document sections
3. Quote relevant text excerpts in referenced_clauses
4. Provide clear reasoning for each referenced clause
5. If multiple clauses are relevant, include up to 3 most important ones
6. Be precise and factual in your justification
7. Include any relevant conditions, limitations, or exceptions in additional_info
8. Return ONLY the JSON object, no additional text

## RESPONSE:"""
        
        return prompt
    
    def _make_request_with_backoff(self, provider: LLMProvider, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Make request with exponential backoff for rate limiting"""
        for attempt in range(max_retries):
            try:
                # Add exponential backoff delay
                if attempt > 0:
                    delay = (2 ** attempt) + random.uniform(0, 1)  # 2s, 4s, 8s + jitter
                    logger.info(f"⏳ Attempt {attempt + 1}/{max_retries} - waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                
                return provider.generate_response(
                    prompt,
                    max_tokens=2000,
                    temperature=0.2
                )
                
            except Exception as e:
                error_msg = str(e)
                is_rate_limit = "429" in error_msg or "rate limit" in error_msg.lower()
                
                if is_rate_limit and attempt < max_retries - 1:
                    logger.warning(f"🚦 {provider.provider_name} rate limited on attempt {attempt + 1}, retrying...")
                    continue
                else:
                    # Last attempt or non-rate-limit error
                    logger.error(f"❌ {provider.provider_name} failed on attempt {attempt + 1}: {error_msg}")
                    raise
        
        return None
    
    def analyze_document_query(self, query: str, relevant_chunks: List[Dict]) -> Dict[str, Any]:
        """Analyze query using all Groq providers first, then Together AI as backup"""
        
        if not relevant_chunks:
            return {
                "direct_answer": "I couldn't find relevant information in the document to answer your question.",
                "decision": "Uncertain",
                "justification": "No relevant information found in the document to answer this query.",
                "referenced_clauses": [],
                "additional_info": "Please ensure your question is related to the content of the uploaded document."
            }
        
        prompt = self.create_reasoning_prompt(query, relevant_chunks)
        logger.info(f"📝 Processing query: {query[:100]}...")
        
        # Build provider priority list: All available Groq providers first, then Together AI
        provider_priority = []
        
        # Add all available Groq providers first
        for groq_provider in self.groq_providers:
            if not groq_provider.is_rate_limited():
                provider_priority.append(groq_provider)
        
        # Add Together AI as backup if available
        if self.together_provider and not self.together_provider.is_rate_limited():
            provider_priority.append(self.together_provider)
        
        # If all are rate limited, try them anyway (emergency fallback)
        if not provider_priority:
            logger.warning("⚠️ All providers are rate limited, trying emergency fallback...")
            provider_priority.extend(self.groq_providers)
            if self.together_provider:
                provider_priority.append(self.together_provider)
        
        if not provider_priority:
            logger.error("❌ No providers available")
            return self._create_enhanced_error_response("No AI providers available", query, relevant_chunks)
        
        last_error = None
        
        # Try each provider in priority order
        for provider in provider_priority:
            try:
                logger.info(f"🚀 Trying {provider.provider_name}...")
                
                # Small delay if provider was recently rate limited
                if provider.last_rate_limit_time and time.time() - provider.last_rate_limit_time < 5:
                    logger.info(f"⏳ Adding small delay for {provider.provider_name} recovery...")
                    time.sleep(1)
                
                raw_response = provider.generate_response(
                    prompt,
                    max_tokens=2000,
                    temperature=0.1  # Lower temperature for consistent JSON
                )
                
                logger.info(f"✅ Response received from {provider.provider_name}: {raw_response[:200]}...")
                
                # Parse and validate JSON response
                try:
                    cleaned_response = self._clean_json_response(raw_response)
                    response_data = json.loads(cleaned_response)
                    
                    if self._validate_response_structure(response_data):
                        if "Together" in provider.provider_name:
                            logger.info(f"🎯 Successfully used backup provider: {provider.provider_name}")
                        else:
                            logger.info(f"⚡ Successfully used Groq provider: {provider.provider_name}")
                        return response_data
                    else:
                        logger.warning(f"❌ Invalid response structure from {provider.provider_name}")
                        continue
                        
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON parsing failed for {provider.provider_name}: {str(e)}")
                    last_error = f"JSON parsing error from {provider.provider_name}"
                    continue
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ {provider.provider_name} failed: {error_msg}")
                last_error = error_msg
                
                # Log rate limit specifically
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    logger.warning(f"🚦 {provider.provider_name} hit rate limit, trying next provider...")
                
                continue
        
        # All providers failed
        logger.error("🚨 All providers failed")
        return self._create_enhanced_error_response(last_error or "All providers failed", query, relevant_chunks)
    
    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to extract valid JSON"""
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        # Find the first { and last }
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start != -1 and end != 0:
            return response[start:end]
        
        return response
    
    def _validate_response_structure(self, response: Dict) -> bool:
        """Validate that response has required structure"""
        required_keys = ["direct_answer", "decision", "justification", "referenced_clauses", "additional_info"]
        
        if not all(key in response for key in required_keys):
            return False
        
        valid_decisions = ["Approved", "Denied", "Uncertain"]
        if response["decision"] not in valid_decisions:
            return False
        
        if not isinstance(response["referenced_clauses"], list):
            return False
        
        for clause in response["referenced_clauses"]:
            if not isinstance(clause, dict):
                return False
            clause_keys = ["clause_id", "text", "reasoning"]
            if not all(key in clause for key in clause_keys):
                return False
        
        return True
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response when LLM is completely unavailable"""
        return {
            "direct_answer": "I'm unable to process your question due to a system error.",
            "decision": "Uncertain",
            "justification": f"Unable to process query due to system error: {error_message}",
            "referenced_clauses": [],
            "additional_info": "Please try again later or contact support if the issue persists."
        }
    
    def _create_enhanced_error_response(self, error_message: str, query: str, chunks: List[Dict]) -> Dict[str, Any]:
        """Create enhanced error response that includes document content when possible"""
        referenced_clauses = []
        
        # Still try to show document content even when AI fails
        for chunk in chunks[:3]:  # Take top 3 chunks
            clause = {
                "clause_id": chunk.get("clause_id", chunk.get("chunk_id", "Unknown")),
                "text": chunk["text"][:300] + "..." if len(chunk["text"]) > 300 else chunk["text"],
                "reasoning": f"Relevant content with similarity score: {chunk.get('similarity_score', 0):.3f}"
            }
            referenced_clauses.append(clause)
        
        # Provide specific guidance based on error type
        if "429" in error_message or "rate limit" in error_message.lower() or "too many requests" in error_message.lower():
            direct_answer = "🚦 Both Groq and Together AI are temporarily busy - here's what I found in your document"
            additional_info = "Both AI providers are experiencing high demand. The relevant document sections are shown above. Please try again in a moment."
        else:
            direct_answer = "⚠️ System error occurred - here's what I found in your document"
            additional_info = "A technical error occurred with both AI providers, but I've extracted the most relevant sections from your document above."
        
        return {
            "direct_answer": direct_answer if referenced_clauses else "I'm unable to process your question due to a system error.",
            "decision": "Uncertain",
            "justification": f"System error prevented AI analysis: {error_message}. However, relevant document sections have been identified based on similarity matching.",
            "referenced_clauses": referenced_clauses,
            "additional_info": additional_info
        }
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current status of all providers"""
        status = {}
        
        # Status for all Groq providers
        for i, provider in enumerate(self.groq_providers, 1):
            status[f"groq_{i}"] = {
                "available": not provider.is_rate_limited(),
                "rate_limited": provider.is_rate_limited(),
                "consecutive_failures": provider.consecutive_failures,
                "model": provider.model_name,
                "last_rate_limit_time": provider.last_rate_limit_time,
                "provider_type": "primary"
            }
        
        # Add empty slots for missing Groq providers
        for i in range(len(self.groq_providers) + 1, 4):
            status[f"groq_{i}"] = {
                "available": False,
                "rate_limited": False,
                "consecutive_failures": 0,
                "model": "Not configured",
                "last_rate_limit_time": None,
                "provider_type": "primary"
            }
        
        # Status for Together AI backup
        if self.together_provider:
            status["together"] = {
                "available": not self.together_provider.is_rate_limited(),
                "rate_limited": self.together_provider.is_rate_limited(),
                "consecutive_failures": self.together_provider.consecutive_failures,
                "model": self.together_provider.model_name,
                "last_rate_limit_time": self.together_provider.last_rate_limit_time,
                "provider_type": "backup"
            }
        else:
            status["together"] = {
                "available": False,
                "rate_limited": False,
                "consecutive_failures": 0,
                "model": "Not configured",
                "last_rate_limit_time": None,
                "provider_type": "backup"
            }
        
        return status
