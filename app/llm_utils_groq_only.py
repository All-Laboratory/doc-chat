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

class GroqProvider:
    """Groq provider - Ultra fast, no retries"""
    
    def __init__(self, api_key: str, model_name: str = "llama3-8b-8192", provider_id: str = "Groq"):
        self.api_key = api_key
        self.model_name = model_name
        self.provider_name = provider_id
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.last_429_time = None
        self.consecutive_failures = 0
    
    def is_likely_rate_limited(self) -> bool:
        """Quick check if provider might be rate limited"""
        if self.last_429_time is None:
            return False
        
        # Consider provider risky for 45 seconds after 429
        time_since_429 = time.time() - self.last_429_time
        return time_since_429 < 45
    
    def mark_429_error(self):
        """Mark that this provider hit 429 - no retries, just track"""
        self.last_429_time = time.time()
        self.consecutive_failures += 1
        logger.info(f"⚡ {self.provider_name} hit 429 - switching to next Groq key immediately")
    
    def mark_success(self):
        """Reset failure counter on success"""
        self.consecutive_failures = 0
    
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
        
        # Mark success
        self.mark_success()
        
        return result["choices"][0]["message"]["content"].strip()

class MultiKeyGroqProvider:
    """Multiple Groq API keys for maximum throughput - GROQ ONLY"""
    
    def __init__(self, api_keys: List[str], model_name: str = "llama3-8b-8192"):
        self.providers = []
        self.model_name = model_name
        
        for i, key in enumerate(api_keys):
            if key and key not in ["your_actual_groq_api_key_here", "your_groq_api_key"]:
                provider = GroqProvider(key, model_name, f"Groq-Key-{i+1}")
                self.providers.append(provider)
        
        if not self.providers:
            raise ValueError("No valid Groq API keys found!")
        
        logger.info(f"🚀 GROQ-ONLY System: Initialized {len(self.providers)} Groq keys")
        logger.info(f"⚡ Total capacity: {len(self.providers) * 30} requests/minute")
    
    def get_best_provider(self) -> Optional[GroqProvider]:
        """Get the provider least likely to be rate limited"""
        # First try providers that haven't been rate limited
        available = [p for p in self.providers if not p.is_likely_rate_limited()]
        
        if available:
            # Sort by consecutive failures (fewer failures first)
            available.sort(key=lambda p: p.consecutive_failures)
            return available[0]
        
        # If all are rate limited, use the one with oldest 429 time
        if self.providers:
            return min(self.providers, key=lambda p: p.last_429_time or 0)
        
        return None
    
    def get_next_available_providers(self) -> List[GroqProvider]:
        """Get list of all providers sorted by availability"""
        # Sort providers by: not rate limited first, then by failure count, then by last 429 time
        def sort_key(provider):
            is_rate_limited = provider.is_likely_rate_limited()
            return (
                is_rate_limited,  # False (not rate limited) comes before True
                provider.consecutive_failures,
                provider.last_429_time or 0
            )
        
        return sorted(self.providers, key=sort_key)

class DocumentReasoningLLM:
    """GROQ-ONLY SYSTEM - Multiple Groq keys, no other providers"""
    
    def __init__(self):
        self.groq_multi = self._initialize_groq_multi()
        
        logger.info("🚀 GROQ-ONLY LLM System initialized")
        logger.info("⚡ Strategy: Multiple Groq keys with instant rotation")
        logger.info(f"📊 Capacity: {len(self.groq_multi.providers) * 30} requests/minute")
    
    def _initialize_groq_multi(self) -> MultiKeyGroqProvider:
        """Initialize multiple Groq keys"""
        keys = []
        
        # Try to get multiple keys
        for i in range(1, 6):  # Support up to 5 keys
            key_name = f"GROQ_API_KEY_{i}" if i > 1 else "GROQ_API_KEY"
            key = os.getenv(key_name)
            if key and key not in ["your_actual_groq_api_key_here", "your_groq_api_key"]:
                keys.append(key)
        
        if not keys:
            raise ValueError("No valid GROQ API keys found. Set GROQ_API_KEY, GROQ_API_KEY_2, GROQ_API_KEY_3 in environment")
        
        model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        return MultiKeyGroqProvider(keys, model)
    
    def analyze_document_query(self, query: str, relevant_chunks: List[Dict]) -> Dict[str, Any]:
        """Fast analysis - GROQ ONLY, NO FALLBACKS"""
        
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
        
        # Get all available Groq providers sorted by best availability
        providers_to_try = self.groq_multi.get_next_available_providers()
        
        if not providers_to_try:
            return self._create_error_response("No Groq providers available")
        
        logger.info(f"🔄 Will try {len(providers_to_try)} Groq keys if needed")
        
        # Try each Groq provider with smart retries (max 2 attempts per key)
        for provider in providers_to_try:
            max_attempts = 2  # Retry each key once if it fails
            
            for attempt in range(max_attempts):
                try:
                    attempt_info = f"(attempt {attempt + 1}/{max_attempts})" if max_attempts > 1 else ""
                    logger.info(f"⚡ Trying {provider.provider_name} {attempt_info}...")
                    
                    raw_response = provider.generate_response(
                        prompt,
                        max_tokens=2000,
                        temperature=0.1 + (attempt * 0.1)  # Slightly increase temperature on retry
                    )
                    
                    logger.info(f"✅ {provider.provider_name} responded successfully")
                    
                    # Parse JSON
                    cleaned_response = self._clean_json_response(raw_response)
                    response_data = json.loads(cleaned_response)
                    
                    if self._validate_response_structure(response_data):
                        logger.info(f"🎯 Success with {provider.provider_name} on attempt {attempt + 1}")
                        return response_data
                    else:
                        logger.warning(f"❌ Invalid response structure from {provider.provider_name} (attempt {attempt + 1})")
                        if attempt < max_attempts - 1:
                            logger.info(f"🔄 Retrying {provider.provider_name} with adjusted parameters...")
                            time.sleep(0.5)  # Brief pause before retry
                            continue
                        else:
                            break  # Move to next provider
                        
                except requests.exceptions.RequestException as e:
                    if "429" in str(e):
                        logger.info(f"⚡ {provider.provider_name} hit 429 on attempt {attempt + 1} - trying next key")
                        break  # Don't retry 429 errors, move to next key
                    else:
                        logger.error(f"❌ {provider.provider_name} failed on attempt {attempt + 1}: {str(e)}")
                        if attempt < max_attempts - 1:
                            logger.info(f"🔄 Retrying {provider.provider_name} after error...")
                            time.sleep(1.0)  # Pause before retry on error
                            continue
                        else:
                            break
                
                except json.JSONDecodeError:
                    logger.error(f"❌ {provider.provider_name} returned invalid JSON on attempt {attempt + 1}")
                    if attempt < max_attempts - 1:
                        logger.info(f"🔄 Retrying {provider.provider_name} for better JSON...")
                        time.sleep(0.5)
                        continue
                    else:
                        break
                
                except Exception as e:
                    logger.error(f"❌ {provider.provider_name} unexpected error on attempt {attempt + 1}: {str(e)}")
                    if attempt < max_attempts - 1:
                        logger.info(f"🔄 Retrying {provider.provider_name} after unexpected error...")
                        time.sleep(1.0)
                        continue
                    else:
                        break
        
        # All Groq providers failed - return enhanced error with document content
        logger.error("🚨 All Groq keys failed - showing document content")
        return self._create_enhanced_error_response("All Groq keys failed", query, relevant_chunks)
    
    def create_reasoning_prompt(self, query: str, relevant_chunks: List[Dict]) -> str:
        """Create structured prompt optimized for Groq"""
        context_sections = []
        for i, chunk in enumerate(relevant_chunks[:5], 1):
            clause_id = chunk.get("clause_id", f"Section {i}")
            text = chunk["text"][:1000]
            context_sections.append(f"### {clause_id}\n{text}")
        
        context = "\n".join(context_sections)
        
        return f"""You are an expert document analysis assistant. Analyze the document and provide a JSON response.

## CONTEXT FROM DOCUMENT:
{context}

## USER QUERY:
{query}

## INSTRUCTIONS:
Respond with a valid JSON object in this exact format:

{{
  "direct_answer": "A comprehensive, detailed answer to the user's question including specific information from the document. Include relevant details such as time periods, amounts, conditions, limitations, and any other important specifics mentioned in the document. The answer should be complete and informative, not just a brief response.",
  "decision": "Approved" | "Denied" | "Uncertain",
  "justification": "Detailed reasoning based on the document analysis, explaining how the document supports the answer with specific references to relevant clauses, conditions, and requirements",
  "referenced_clauses": [
    {{
      "clause_id": "section identifier from document",
      "text": "relevant excerpt from the clause",
      "reasoning": "detailed explanation of why this clause is relevant to the decision and how it supports the answer"
    }}
  ],
  "additional_info": "Any additional relevant information, conditions, limitations, or related details from the document that provide context or important supplementary information"
}}

## ANSWER REQUIREMENTS:
- Provide DETAILED, COMPREHENSIVE answers, not brief responses
- Include specific information like time periods, amounts, percentages, conditions, and limitations
- Reference exact requirements, waiting periods, coverage limits, and eligibility criteria
- Explain the full context of the answer with supporting details from the document
- If the document specifies conditions or exceptions, include them in your answer
- Make the answer self-contained and informative

## DECISION CRITERIA:
- **Approved**: The document clearly supports the request/claim
- **Denied**: The document explicitly prohibits or excludes the request/claim
- **Uncertain**: The document is ambiguous or lacks specific details

IMPORTANT: Return ONLY the JSON object. No markdown, no explanations, no additional text."""
    
    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to extract valid JSON"""
        response = response.strip()
        
        # Remove markdown code blocks
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
        """Create error response when all Groq providers fail"""
        return {
            "direct_answer": "I'm unable to process your question due to a system error.",
            "decision": "Uncertain",
            "justification": f"System error: {error_message}",
            "referenced_clauses": [],
            "additional_info": "Please try again in a moment - all Groq keys may be temporarily busy."
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
            "direct_answer": "🚨 All Groq keys are temporarily busy - here's what I found in your document",
            "decision": "Uncertain",
            "justification": f"System error: {error_message}. However, relevant document sections have been identified based on similarity matching.",
            "referenced_clauses": referenced_clauses,
            "additional_info": "All Groq API keys are temporarily at capacity. The relevant document sections are shown above. Please try again in a moment."
        }
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get current status of all Groq providers"""
        providers_status = []
        
        for provider in self.groq_multi.providers:
            status = {
                "name": provider.provider_name,
                "available": not provider.is_likely_rate_limited(),
                "rate_limited": provider.is_likely_rate_limited(),
                "consecutive_failures": provider.consecutive_failures,
                "model": provider.model_name,
                "last_rate_limit_time": provider.last_429_time
            }
            providers_status.append(status)
        
        # Calculate totals
        available_count = sum(1 for p in providers_status if p["available"])
        total_capacity = len(providers_status) * 30  # 30 req/min per key
        available_capacity = available_count * 30
        
        return {
            "strategy": "Groq-Only Multi-Key System",
            "total_keys": len(providers_status),
            "available_keys": available_count,
            "total_capacity_per_minute": total_capacity,
            "available_capacity_per_minute": available_capacity,
            "providers": providers_status
        }
