import os
import json
import logging
import requests
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider:
    """Base class for LLM providers - NO RETRIES, NO SLEEP"""
    
    def __init__(self, api_key: str, model_name: str, provider_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self.provider_name = provider_name
        self.last_429_time = None
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError
    
    def is_likely_rate_limited(self) -> bool:
        """Quick check if provider might be rate limited (avoid 429s)"""
        if self.last_429_time is None:
            return False
        
        # Consider provider risky for 30 seconds after 429
        time_since_429 = time.time() - self.last_429_time
        return time_since_429 < 30
    
    def mark_429_error(self):
        """Mark that this provider hit 429 - no retries, just track"""
        self.last_429_time = time.time()
        logger.info(f"⚡ {self.provider_name} hit 429 - moving to next provider immediately")

class GroqProvider(LLMProvider):
    """Groq provider - Ultra fast, no retries"""
    
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
        
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 429:
            self.mark_429_error()
            raise requests.exceptions.RequestException(f"429 Rate limit - {self.provider_name}")
        
        response.raise_for_status()
        result = response.json()
        
        return result["choices"][0]["message"]["content"].strip()

class TogetherAIProvider(LLMProvider):
    """Together AI provider - Reliable backup"""
    
    def __init__(self, api_key: str, model_name: str):
        super().__init__(api_key, model_name, "Together AI")
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
        
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 429:
            self.mark_429_error()
            raise requests.exceptions.RequestException(f"429 Rate limit - {self.provider_name}")
        
        response.raise_for_status()
        result = response.json()
        
        if self.is_chat_model:
            return result["choices"][0]["message"]["content"].strip()
        else:
            return result["output"]["choices"][0]["text"].strip()

class MultiKeyGroqProvider:
    """Multiple Groq API keys for higher throughput - NO 429 ERRORS"""
    
    def __init__(self, api_keys: List[str], model_name: str = "llama3-8b-8192"):
        self.providers = []
        for i, key in enumerate(api_keys):
            if key and key not in ["your_actual_groq_api_key_here", "your_groq_api_key"]:
                provider = GroqProvider(key, model_name)
                provider.provider_name = f"Groq-Key-{i+1}"
                self.providers.append(provider)
        
        logger.info(f"✅ Initialized {len(self.providers)} Groq keys")
    
    def get_best_provider(self) -> Optional[GroqProvider]:
        """Get the provider least likely to be rate limited"""
        # Sort by last 429 time (oldest first)
        available = [p for p in self.providers if not p.is_likely_rate_limited()]
        
        if available:
            return available[0]  # Use the freshest one
        
        # If all are rate limited, use the oldest 429
        if self.providers:
            return min(self.providers, key=lambda p: p.last_429_time or 0)
        
        return None

class DocumentReasoningLLM:
    """NO RETRY SYSTEM - Instant failover between providers"""
    
    def __init__(self):
        self.groq_multi = self._initialize_groq_multi()
        self.together_provider = self._initialize_together()
        
        if not self.groq_multi.providers and not self.together_provider:
            raise ValueError("Need at least one working API key")
        
        logger.info("🚀 NO-RETRY LLM System initialized")
        logger.info("⚡ Strategy: Instant failover, no sleep/retry delays")
    
    def _initialize_groq_multi(self) -> MultiKeyGroqProvider:
        """Initialize multiple Groq keys"""
        keys = []
        
        # Try to get multiple keys
        for i in range(1, 6):  # Support up to 5 keys
            key_name = f"GROQ_API_KEY_{i}" if i > 1 else "GROQ_API_KEY"
            key = os.getenv(key_name)
            if key:
                keys.append(key)
        
        model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        return MultiKeyGroqProvider(keys, model)
    
    def _initialize_together(self) -> Optional[TogetherAIProvider]:
        """Initialize Together AI provider"""
        together_key = os.getenv("TOGETHER_API_KEY")
        if together_key and together_key not in ["your_together_api_key", "your_actual_api_key"]:
            model = os.getenv("TOGETHER_MODEL", "moonshotai/kimi-k2-instruct")
            try:
                provider = TogetherAIProvider(together_key, model)
                logger.info(f"✅ Together AI initialized: {model}")
                return provider
            except Exception as e:
                logger.error(f"❌ Together AI failed: {e}")
                return None
        return None
    
    def analyze_document_query(self, query: str, relevant_chunks: List[Dict]) -> Dict[str, Any]:
        """Fast analysis - NO RETRIES, NO SLEEP"""
        
        if not relevant_chunks:
            return {
                "direct_answer": "I couldn't find relevant information in the document.",
                "decision": "Uncertain",
                "justification": "No relevant information found.",
                "referenced_clauses": [],
                "additional_info": "Please ensure your question relates to the uploaded document."
            }
        
        prompt = self.create_reasoning_prompt(query, relevant_chunks)
        logger.info(f"📝 Processing query: {query[:100]}...")
        
        # Build provider list (no retries, just try each once)
        providers_to_try = []
        
        # Add best Groq provider first
        best_groq = self.groq_multi.get_best_provider()
        if best_groq:
            providers_to_try.append(("Groq", best_groq))
        
        # Add Together AI as immediate fallback
        if self.together_provider and not self.together_provider.is_likely_rate_limited():
            providers_to_try.append(("Together AI", self.together_provider))
        
        # Add any remaining Groq keys
        for provider in self.groq_multi.providers:
            if provider != best_groq and not provider.is_likely_rate_limited():
                providers_to_try.append((provider.provider_name, provider))
        
        if not providers_to_try:
            return self._create_error_response("All providers temporarily unavailable")
        
        # Try each provider ONCE - no retries
        for provider_name, provider in providers_to_try:
            try:
                logger.info(f"⚡ Trying {provider_name}...")
                
                raw_response = provider.generate_response(
                    prompt,
                    max_tokens=2000,
                    temperature=0.2
                )
                
                logger.info(f"✅ {provider_name} responded successfully")
                
                # Parse JSON
                cleaned_response = self._clean_json_response(raw_response)
                response_data = json.loads(cleaned_response)
                
                if self._validate_response_structure(response_data):
                    return response_data
                else:
                    logger.warning(f"❌ Invalid response from {provider_name}")
                    continue
                    
            except requests.exceptions.RequestException as e:
                if "429" in str(e):
                    logger.info(f"⚡ {provider_name} hit 429 - trying next provider")
                else:
                    logger.error(f"❌ {provider_name} failed: {str(e)}")
                continue
            
            except json.JSONDecodeError:
                logger.error(f"❌ {provider_name} returned invalid JSON")
                continue
            
            except Exception as e:
                logger.error(f"❌ {provider_name} unexpected error: {str(e)}")
                continue
        
        # All providers failed - return enhanced error with document content
        return self._create_enhanced_error_response("All providers failed", query, relevant_chunks)
    
    def create_reasoning_prompt(self, query: str, relevant_chunks: List[Dict]) -> str:
        """Create structured prompt for document reasoning"""
        context_sections = []
        for i, chunk in enumerate(relevant_chunks[:5], 1):
            clause_id = chunk.get("clause_id", f"Section {i}")
            text = chunk["text"][:1000]
            context_sections.append(f"### {clause_id}\n{text}")
        
        context = "\n".join(context_sections)
        
        return f"""You are an expert document analysis assistant. Analyze the document and answer the query.

## CONTEXT FROM DOCUMENT:
{context}

## USER QUERY:
{query}

## INSTRUCTIONS:
Respond with a valid JSON object in exactly this format:

{{
  "direct_answer": "A concise, direct answer to the user's question",
  "decision": "Approved" | "Denied" | "Uncertain",
  "justification": "Clear reasoning based on the document analysis",
  "referenced_clauses": [
    {{
      "clause_id": "section identifier from document",
      "text": "relevant excerpt from the clause",
      "reasoning": "why this clause is relevant to the decision"
    }}
  ],
  "additional_info": "Any additional relevant information or conditions"
}}

## DECISION CRITERIA:
- **Approved**: The document clearly supports the request/claim
- **Denied**: The document explicitly prohibits or excludes the request/claim
- **Uncertain**: The document is ambiguous or lacks specific details

Return ONLY the JSON object, no additional text, no markdown formatting, no explanations."""
    
    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to extract valid JSON"""
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start != -1 and end != 0:
            return response[start:end]
        
        return response
    
    def _validate_response_structure(self, response: Dict) -> bool:
        """Validate response has required structure"""
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
        """Create error response when all providers fail"""
        return {
            "direct_answer": "I'm unable to process your question due to a system error.",
            "decision": "Uncertain",
            "justification": f"System error: {error_message}",
            "referenced_clauses": [],
            "additional_info": "Please try again in a moment."
        }
    
    def _create_enhanced_error_response(self, error_message: str, query: str, chunks: List[Dict]) -> Dict[str, Any]:
        """Enhanced error response with document content"""
        referenced_clauses = []
        
        for chunk in chunks[:3]:
            clause = {
                "clause_id": chunk.get("clause_id", chunk.get("chunk_id", "Unknown")),
                "text": chunk["text"][:300] + "..." if len(chunk["text"]) > 300 else chunk["text"],
                "reasoning": f"Relevant content (similarity: {chunk.get('similarity_score', 0):.3f})"
            }
            referenced_clauses.append(clause)
        
        return {
            "direct_answer": "System error occurred - here's what I found in your document",
            "decision": "Uncertain", 
            "justification": f"System error: {error_message}. Relevant document sections identified.",
            "referenced_clauses": referenced_clauses,
            "additional_info": "Technical error occurred but relevant document content is shown above."
        }
