import os
import json
import logging
import requests
import time
import random
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider:
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: str, model_name: str, provider_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self.provider_name = provider_name
        self.last_rate_limit_time = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError
    
    def is_rate_limited(self) -> bool:
        """Check if this provider is currently rate limited"""
        if self.last_rate_limit_time is None:
            return False
        
        # Consider provider rate limited for 60 seconds after last rate limit
        time_since_rate_limit = time.time() - self.last_rate_limit_time
        return time_since_rate_limit < 60
    
    def mark_rate_limited(self):
        """Mark this provider as rate limited"""
        self.last_rate_limit_time = time.time()
        self.consecutive_failures += 1
        logger.warning(f"{self.provider_name} marked as rate limited. Consecutive failures: {self.consecutive_failures}")
    
    def mark_success(self):
        """Mark successful request to reset failure counter"""
        self.consecutive_failures = 0
    
    def is_temporarily_disabled(self) -> bool:
        """Check if provider should be temporarily disabled due to too many failures"""
        return self.consecutive_failures >= self.max_consecutive_failures

class TogetherAIProvider(LLMProvider):
    """Together AI provider for various models including Moonshot Kimi"""
    
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

class GroqProvider(LLMProvider):
    """Groq provider for fast inference"""
    
    def __init__(self, api_key: str, model_name: str = "llama3-70b-8192"):
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

class FireworksProvider(LLMProvider):
    """Fireworks AI provider"""
    
    def __init__(self, api_key: str, model_name: str):
        super().__init__(api_key, model_name, "Fireworks AI")
        self.base_url = "https://api.fireworks.ai/inference/v1/completions"
    
    def generate_response(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
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
            
            return result["choices"][0]["text"].strip()
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            # Check if it's a rate limit error
            if "429" in error_msg or "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                self.mark_rate_limited()
            logger.error(f"Fireworks AI API request failed: {error_msg}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected Fireworks response format: {str(e)}")
            raise

class OpenAIProvider(LLMProvider):
    """OpenAI provider for GPT models"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        super().__init__(api_key, model_name, "OpenAI")
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
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
            logger.error(f"OpenAI API request failed: {error_msg}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected OpenAI response format: {str(e)}")
            raise

class DocumentReasoningLLM:
    """Enhanced LLM class with intelligent rate limit handling and fallback"""
    
    def __init__(self):
        self.providers = self._initialize_all_providers()
        self.primary_provider_name = os.getenv("LLM_PROVIDER", "together").lower()
        
        # Filter out providers without valid API keys
        self.active_providers = {k: v for k, v in self.providers.items() if v is not None}
        
        if not self.active_providers:
            raise ValueError("No valid API keys found. Please set at least one API key.")
        
        # Set primary provider
        if self.primary_provider_name in self.active_providers:
            self.primary_provider = self.active_providers[self.primary_provider_name]
        else:
            # Fallback to first available provider
            self.primary_provider_name = list(self.active_providers.keys())[0]
            self.primary_provider = self.active_providers[self.primary_provider_name]
        
        logger.info(f"Initialized Enhanced LLM with primary: {self.primary_provider_name}")
        logger.info(f"Available fallback providers: {list(self.active_providers.keys())}")
    
    def _initialize_all_providers(self) -> Dict[str, Optional[LLMProvider]]:
        """Initialize all available providers"""
        providers = {}
        
        # Together AI
        together_key = os.getenv("TOGETHER_API_KEY")
        if together_key and together_key not in ["your_together_api_key", "your_actual_api_key"]:
            model = os.getenv("TOGETHER_MODEL", "moonshotai/kimi-k2-instruct")
            try:
                providers["together"] = TogetherAIProvider(together_key, model)
                logger.info("✅ Together AI provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Together AI: {e}")
                providers["together"] = None
        else:
            providers["together"] = None
        
        # Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and groq_key not in ["your_actual_groq_api_key_here", "your_groq_api_key"]:
            model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
            try:
                providers["groq"] = GroqProvider(groq_key, model)
                logger.info("✅ Groq provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Groq: {e}")
                providers["groq"] = None
        else:
            providers["groq"] = None
        
        # Fireworks
        fireworks_key = os.getenv("FIREWORKS_API_KEY")
        if fireworks_key and fireworks_key not in ["your_fireworks_api_key", "your_actual_api_key"]:
            model = os.getenv("FIREWORKS_MODEL", "accounts/fireworks/models/llama-v2-7b-chat")
            try:
                providers["fireworks"] = FireworksProvider(fireworks_key, model)
                logger.info("✅ Fireworks AI provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Fireworks: {e}")
                providers["fireworks"] = None
        else:
            providers["fireworks"] = None
        
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key not in ["your_openai_api_key", "your_actual_api_key"]:
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            try:
                providers["openai"] = OpenAIProvider(openai_key, model)
                logger.info("✅ OpenAI provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
                providers["openai"] = None
        else:
            providers["openai"] = None
        
        return providers
    
    def _get_available_providers(self) -> List[Tuple[str, LLMProvider]]:
        """Get list of available providers, excluding rate-limited and disabled ones"""
        available = []
        
        # Start with primary provider if available
        if (self.primary_provider and 
            not self.primary_provider.is_rate_limited() and 
            not self.primary_provider.is_temporarily_disabled()):
            available.append((self.primary_provider_name, self.primary_provider))
        
        # Add other providers
        for name, provider in self.active_providers.items():
            if (name != self.primary_provider_name and 
                provider and 
                not provider.is_rate_limited() and 
                not provider.is_temporarily_disabled()):
                available.append((name, provider))
        
        # If all providers are rate limited or disabled, include them anyway but log warning
        if not available:
            logger.warning("All providers are rate limited or disabled. Including all providers as fallbacks.")
            available = [(name, provider) for name, provider in self.active_providers.items() if provider]
        
        return available
    
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
    
    def analyze_document_query(self, query: str, relevant_chunks: List[Dict]) -> Dict[str, Any]:
        """Analyze query with intelligent rate limit handling and provider fallbacks"""
        
        if not relevant_chunks:
            return {
                "direct_answer": "I couldn't find relevant information in the document to answer your question.",
                "decision": "Uncertain",
                "justification": "No relevant information found in the document to answer this query.",
                "referenced_clauses": [],
                "additional_info": "Please ensure your question is related to the content of the uploaded document."
            }
        
        prompt = self.create_reasoning_prompt(query, relevant_chunks)
        logger.info(f"Processing query: {query[:100]}...")
        
        # Get available providers in priority order
        available_providers = self._get_available_providers()
        
        if not available_providers:
            logger.error("No providers available")
            return self._create_error_response("All AI providers are currently unavailable")
        
        last_error = None
        
        # Try each available provider
        for provider_name, provider in available_providers:
            try:
                logger.info(f"🚀 Attempting with {provider_name} provider...")
                
                # Add small random delay for rate limit management
                if provider.last_rate_limit_time:
                    time.sleep(random.uniform(0.5, 1.5))
                
                raw_response = provider.generate_response(
                    prompt,
                    max_tokens=2000,
                    temperature=0.2
                )
                
                logger.info(f"✅ Response received from {provider_name}: {raw_response[:200]}...")
                
                # Parse and validate JSON response
                try:
                    cleaned_response = self._clean_json_response(raw_response)
                    response_data = json.loads(cleaned_response)
                    
                    if self._validate_response_structure(response_data):
                        if provider_name != self.primary_provider_name:
                            logger.info(f"🎯 Successfully used fallback provider: {provider_name}")
                        else:
                            logger.info(f"✅ Successfully used primary provider: {provider_name}")
                        return response_data
                    else:
                        logger.warning(f"❌ Invalid response structure from {provider_name}")
                        continue
                        
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON parsing failed for {provider_name}: {str(e)}")
                    last_error = f"JSON parsing error from {provider_name}"
                    continue
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ {provider_name} failed: {error_msg}")
                last_error = error_msg
                
                # If it's a rate limit error, provider has already been marked
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    logger.warning(f"⏰ Rate limit detected for {provider_name}, marked for cooldown")
                
                continue
        
        # All providers failed
        logger.error("🚨 All providers failed to generate response")
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
            direct_answer = "🚦 All AI providers are rate limited - here's what I found in your document"
            additional_info = "All AI services are experiencing high demand. The relevant document sections are shown above. Please try again in a few minutes."
        else:
            direct_answer = "⚠️ System error occurred - here's what I found in your document"
            additional_info = "A technical error occurred, but I've extracted the most relevant sections from your document above."
        
        return {
            "direct_answer": direct_answer if referenced_clauses else "I'm unable to process your question due to a system error.",
            "decision": "Uncertain",
            "justification": f"System error prevented AI analysis: {error_message}. However, relevant document sections have been identified based on similarity matching.",
            "referenced_clauses": referenced_clauses,
            "additional_info": additional_info
        }
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers for monitoring"""
        status = {}
        
        for name, provider in self.active_providers.items():
            if provider:
                status[name] = {
                    "available": not provider.is_rate_limited() and not provider.is_temporarily_disabled(),
                    "rate_limited": provider.is_rate_limited(),
                    "temporarily_disabled": provider.is_temporarily_disabled(),
                    "consecutive_failures": provider.consecutive_failures,
                    "model": provider.model_name,
                    "last_rate_limit_time": provider.last_rate_limit_time
                }
            else:
                status[name] = {
                    "available": False,
                    "rate_limited": False,
                    "temporarily_disabled": True,
                    "consecutive_failures": 0,
                    "model": "Not initialized",
                    "last_rate_limit_time": None
                }
        
        return status
