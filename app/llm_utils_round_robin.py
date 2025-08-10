import os
import json
import logging
import requests
import random
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider:
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError

class TogetherAIProvider(LLMProvider):
    """Together AI provider for various models including Moonshot Kimi"""
    
    def __init__(self, api_key: str, model_name: str):
        super().__init__(api_key, model_name)
        # Support both old inference and new chat endpoints
        # Modern models (Kimi, Llama-3, DeepSeek-R1) use chat endpoint
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
            # Use chat format for modern models like Moonshot Kimi
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9
            }
        else:
            # Use completion format for older models
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
            response.raise_for_status()
            
            result = response.json()
            
            if self.is_chat_model:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return result["output"]["choices"][0]["text"].strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Together AI API request failed: {str(e)}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected Together AI response format: {str(e)}")
            raise

class GroqProvider(LLMProvider):
    """Groq provider for fast inference"""
    
    def __init__(self, api_key: str, model_name: str = "llama3-70b-8192"):
        super().__init__(api_key, model_name)
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def generate_response(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request failed: {str(e)}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected Groq response format: {str(e)}")
            raise

class FireworksProvider(LLMProvider):
    """Fireworks AI provider"""
    
    def __init__(self, api_key: str, model_name: str):
        super().__init__(api_key, model_name)
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
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["text"].strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Fireworks AI API request failed: {str(e)}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected Fireworks response format: {str(e)}")
            raise

class DocumentReasoningLLM:
    """Main LLM class for document reasoning tasks with round-robin provider support"""
    
    def __init__(self):
        # Initialize API keys and models
        self.together_api_key = os.getenv("TOGETHER_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.together_model = os.getenv("TOGETHER_MODEL", "moonshotai/kimi-k2-instruct")
        self.groq_model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        
        # Check which providers are available
        self.has_together = self.together_api_key and self.together_api_key != "your_together_api_key"
        self.has_groq = self.groq_api_key and self.groq_api_key != "your_actual_groq_api_key_here"
        
        if not self.has_together and not self.has_groq:
            raise ValueError("At least one API key (TOGETHER_API_KEY or GROQ_API_KEY) must be set")
        
        # Initialize the provider sequence based on available providers
        self.provider_sequence = self._initialize_provider_sequence()
        self.current_provider_index = 0
        
        # Log the configuration
        if self.has_together and self.has_groq:
            logger.info(f"Initialized round-robin LLM with sequence: Groq → Together → Groq → Together")
        elif self.has_together:
            logger.info(f"Initialized LLM with Together AI only (Groq key not available)")
        else:
            logger.info(f"Initialized LLM with Groq only (Together AI key not available)")
    
    def _initialize_provider_sequence(self) -> List[Tuple[str, LLMProvider]]:
        """Initialize the round-robin provider sequence based on available providers"""
        providers = []
        
        if self.has_together and self.has_groq:
            # Both providers available - use round-robin: Groq → Together → Groq → Together
            providers = [
                ("groq", GroqProvider(self.groq_api_key, self.groq_model)),
                ("together", TogetherAIProvider(self.together_api_key, self.together_model)),
                ("groq", GroqProvider(self.groq_api_key, self.groq_model)),
                ("together", TogetherAIProvider(self.together_api_key, self.together_model))
            ]
        elif self.has_together:
            # Only Together AI available - use it repeatedly
            providers = [
                ("together", TogetherAIProvider(self.together_api_key, self.together_model)),
                ("together", TogetherAIProvider(self.together_api_key, self.together_model)),
                ("together", TogetherAIProvider(self.together_api_key, self.together_model)),
                ("together", TogetherAIProvider(self.together_api_key, self.together_model))
            ]
        elif self.has_groq:
            # Only Groq available - use it repeatedly
            providers = [
                ("groq", GroqProvider(self.groq_api_key, self.groq_model)),
                ("groq", GroqProvider(self.groq_api_key, self.groq_model)),
                ("groq", GroqProvider(self.groq_api_key, self.groq_model)),
                ("groq", GroqProvider(self.groq_api_key, self.groq_model))
            ]
        
        return providers
    
    def get_next_provider(self) -> Tuple[str, LLMProvider]:
        """Get the next provider in the round-robin sequence"""
        provider = self.provider_sequence[self.current_provider_index]
        # Update index for next call, wrapping around if needed
        self.current_provider_index = (self.current_provider_index + 1) % len(self.provider_sequence)
        return provider
    
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
        """Analyze query against document chunks and return structured response using round-robin providers"""
        
        if not relevant_chunks:
            return {
                "direct_answer": "I couldn't find relevant information in the document to answer your question.",
                "decision": "Uncertain",
                "justification": "No relevant information found in the document to answer this query.",
                "referenced_clauses": [],
                "additional_info": "Please ensure your question is related to the content of the uploaded document."
            }
        
        # Create prompt
        prompt = self.create_reasoning_prompt(query, relevant_chunks)
        
        logger.info(f"Sending query to LLM: {query[:100]}...")
        
        # Get the next provider in the round-robin sequence
        provider_name, provider = self.get_next_provider()
        
        try:
            logger.info(f"Using round-robin provider: {provider_name}...")
            
            # Get response from LLM
            raw_response = provider.generate_response(
                prompt,
                max_tokens=2000,
                temperature=0.2  # Lower temperature for more consistent JSON output
            )
            
            logger.info(f"Received response from {provider_name}: {raw_response[:200]}...")
            
            # Try to parse JSON response
            try:
                # Clean the response - remove any markdown formatting
                cleaned_response = self._clean_json_response(raw_response)
                response_data = json.loads(cleaned_response)
                
                # Validate response structure
                if self._validate_response_structure(response_data):
                    return response_data
                else:
                    logger.warning(f"Invalid response structure from {provider_name}")
                    return self._create_fallback_response(query, relevant_chunks, "Invalid response structure")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response from {provider_name}: {str(e)}")
                logger.error(f"Raw response: {raw_response}")
                return self._create_fallback_response(query, relevant_chunks, "Failed to parse JSON response")
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"{provider_name} provider failed: {error_msg}")
            return self._create_enhanced_error_response(error_msg, query, relevant_chunks)
    
    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to extract valid JSON"""
        # Remove markdown code blocks if present
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
        
        # Validate decision value
        valid_decisions = ["Approved", "Denied", "Uncertain"]
        if response["decision"] not in valid_decisions:
            return False
        
        # Validate referenced_clauses is a list
        if not isinstance(response["referenced_clauses"], list):
            return False
        
        # Validate each clause has required keys
        for clause in response["referenced_clauses"]:
            if not isinstance(clause, dict):
                return False
            clause_keys = ["clause_id", "text", "reasoning"]
            if not all(key in clause for key in clause_keys):
                return False
        
        return True
    
    def _create_fallback_response(self, query: str, chunks: List[Dict], raw_response: str = None) -> Dict[str, Any]:
        """Create fallback response when LLM fails to provide valid JSON"""
        referenced_clauses = []
        
        for chunk in chunks[:3]:  # Take top 3 chunks
            clause = {
                "clause_id": chunk.get("clause_id", chunk.get("chunk_id", "Unknown")),
                "text": chunk["text"][:300] + "..." if len(chunk["text"]) > 300 else chunk["text"],
                "reasoning": f"Relevant content with similarity score: {chunk.get('similarity_score', 0):.3f}"
            }
            referenced_clauses.append(clause)
        
        justification = "Unable to provide definitive analysis due to processing error. "
        if raw_response:
            justification += "Please review the referenced clauses for relevant information."
        else:
            justification += "The document contains relevant information but requires manual review."
        
        return {
            "direct_answer": "I'm unable to provide a definitive answer due to a processing error.",
            "decision": "Uncertain",
            "justification": justification,
            "referenced_clauses": referenced_clauses,
            "additional_info": "Please try rephrasing your question or contact support if the issue persists."
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
            direct_answer = "AI service temporarily overloaded - here's what I found in your document"
            additional_info = "The AI service is experiencing high demand. The relevant document sections are shown above. Please try again in a moment."
        else:
            direct_answer = "System error occurred - here's what I found in your document"
            additional_info = "A technical error occurred, but I've extracted the most relevant sections from your document above."
        
        return {
            "direct_answer": direct_answer if referenced_clauses else "I'm unable to process your question due to a system error.",
            "decision": "Uncertain",
            "justification": f"System error prevented full analysis: {error_message}. However, relevant document sections have been identified.",
            "referenced_clauses": referenced_clauses,
            "additional_info": additional_info
        }
