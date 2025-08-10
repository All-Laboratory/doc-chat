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
    
    def __init__(self, api_key: str, model_name: str = "llama3-8b-8192"):
        super().__init__(api_key, model_name, "Groq")
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
    """Groq-first system: Always try Groq first, Together AI only as fallback"""
    
    def __init__(self):
        self.groq_provider = self._initialize_groq()
        self.together_provider = self._initialize_together()
        
        if not self.groq_provider and not self.together_provider:
            raise ValueError("At least one API key (GROQ_API_KEY or TOGETHER_API_KEY) must be set")
        
        # Log what we have available
        available_providers = []
        if self.groq_provider:
            available_providers.append("Groq (Primary)")
        if self.together_provider:
            available_providers.append("Together AI (Fallback)")
        
        logger.info(f"🚀 Initialized Groq-First LLM with: {', '.join(available_providers)}")
        logger.info(f"📋 Strategy: Always try Groq first, Together AI only as fallback when Groq fails")
        
        # Railway environment optimization
        railway_env = os.getenv("RAILWAY_ENVIRONMENT")
        if railway_env:
            logger.info(f"🚂 Running on Railway environment: {railway_env}")
    
    def _initialize_groq(self) -> Optional[GroqProvider]:
        """Initialize Groq provider if API key is available"""
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and groq_key not in ["your_actual_groq_api_key_here", "your_groq_api_key"]:
            model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
            try:
                provider = GroqProvider(groq_key, model)
                logger.info(f"✅ Groq provider initialized with model: {model}")
                return provider
            except Exception as e:
                logger.error(f"❌ Failed to initialize Groq: {e}")
                return None
        else:
            logger.warning("⚠️ Groq API key not found or invalid")
            return None
    
    def _initialize_together(self) -> Optional[TogetherAIProvider]:
        """Initialize Together AI provider if API key is available"""
        together_key = os.getenv("TOGETHER_API_KEY")
        if together_key and together_key not in ["your_together_api_key", "your_actual_api_key"]:
            model = os.getenv("TOGETHER_MODEL", "moonshotai/kimi-k2-instruct")
            try:
                provider = TogetherAIProvider(together_key, model)
                logger.info(f"✅ Together AI provider initialized with model: {model}")
                return provider
            except Exception as e:
                logger.error(f"❌ Failed to initialize Together AI: {e}")
                return None
        else:
            logger.warning("⚠️ Together AI API key not found or invalid")
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
        """Analyze query using Groq first, Together AI only as fallback"""
        
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
        
        # Always try Groq first if available and not rate limited
        if self.groq_provider and not self.groq_provider.is_rate_limited():
            try:
                logger.info(f"🚀 Trying Groq (primary)...")
                
                raw_response = self._make_request_with_backoff(self.groq_provider, prompt)
                
                if raw_response:
                    logger.info(f"✅ Response received from Groq: {raw_response[:100]}...")
                    
                    # Parse and validate JSON response
                    try:
                        cleaned_response = self._clean_json_response(raw_response)
                        response_data = json.loads(cleaned_response)
                        
                        if self._validate_response_structure(response_data):
                            logger.info(f"🎯 Successfully processed with Groq (primary)")
                            return response_data
                        else:
                            logger.warning(f"❌ Invalid response structure from Groq, trying fallback...")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ JSON parsing failed for Groq: {str(e)}, trying fallback...")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Groq failed after retries: {error_msg}")
                
                # Log rate limit specifically
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    logger.warning(f"🚦 Groq hit persistent rate limit, trying Together AI fallback...")
                else:
                    logger.warning(f"⚠️ Groq error, trying Together AI fallback...")
        elif self.groq_provider and self.groq_provider.is_rate_limited():
            time_remaining = 60 - (time.time() - self.groq_provider.last_rate_limit_time)
            logger.info(f"⏰ Groq still rate limited ({time_remaining:.0f}s remaining), skipping to Together AI...")
        
        # Fallback to Together AI only if Groq failed or is not available
        if self.together_provider and not self.together_provider.is_rate_limited():
            try:
                logger.info(f"🔄 Falling back to Together AI...")
                
                raw_response = self._make_request_with_backoff(self.together_provider, prompt)
                
                if raw_response:
                    logger.info(f"✅ Response received from Together AI: {raw_response[:100]}...")
                    
                    # Parse and validate JSON response
                    try:
                        cleaned_response = self._clean_json_response(raw_response)
                        response_data = json.loads(cleaned_response)
                        
                        if self._validate_response_structure(response_data):
                            logger.info(f"🎯 Successfully processed with Together AI (fallback)")
                            return response_data
                        else:
                            logger.warning(f"❌ Invalid response structure from Together AI")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ JSON parsing failed for Together AI: {str(e)}")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Together AI failed after retries: {error_msg}")
                
                # Log rate limit specifically
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    logger.warning(f"🚦 Together AI also hit persistent rate limit")
        elif self.together_provider and self.together_provider.is_rate_limited():
            time_remaining = 60 - (time.time() - self.together_provider.last_rate_limit_time)
            logger.info(f"⏰ Together AI still rate limited ({time_remaining:.0f}s remaining)...")
        
        # Both providers failed or are rate limited
        if (self.groq_provider and self.groq_provider.is_rate_limited() and 
            self.together_provider and self.together_provider.is_rate_limited()):
            logger.error("🚨 Both Groq and Together AI are rate limited")
            return self._create_enhanced_error_response("Both providers are rate limited", query, relevant_chunks)
        else:
            logger.error("🚨 Both Groq and Together AI failed after retries")
            return self._create_enhanced_error_response("Both providers failed after retries", query, relevant_chunks)
    
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
        """Get current status of both providers"""
        status = {}
        
        if self.groq_provider:
            status["groq"] = {
                "available": not self.groq_provider.is_rate_limited(),
                "rate_limited": self.groq_provider.is_rate_limited(),
                "consecutive_failures": self.groq_provider.consecutive_failures,
                "model": self.groq_provider.model_name,
                "last_rate_limit_time": self.groq_provider.last_rate_limit_time,
                "priority": "Primary"
            }
        else:
            status["groq"] = {
                "available": False,
                "rate_limited": False,
                "consecutive_failures": 0,
                "model": "Not initialized",
                "last_rate_limit_time": None,
                "priority": "Primary (Not Available)"
            }
        
        if self.together_provider:
            status["together"] = {
                "available": not self.together_provider.is_rate_limited(),
                "rate_limited": self.together_provider.is_rate_limited(),
                "consecutive_failures": self.together_provider.consecutive_failures,
                "model": self.together_provider.model_name,
                "last_rate_limit_time": self.together_provider.last_rate_limit_time,
                "priority": "Fallback"
            }
        else:
            status["together"] = {
                "available": False,
                "rate_limited": False,
                "consecutive_failures": 0,
                "model": "Not initialized",
                "last_rate_limit_time": None,
                "priority": "Fallback (Not Available)"
            }
        
        return status
