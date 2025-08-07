import os
import logging
import time
import hashlib
from typing import List, Dict, Tuple, Any, Optional
from dotenv import load_dotenv
import re

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentChunker:
    """Handle document chunking with overlaps - MINIMAL VERSION"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.warning("🚨 MINIMAL MODE: Basic text chunking only, no ML-powered features")
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Split text into overlapping chunks"""
        if not text or not text.strip():
            return []
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If not the last chunk, try to break at sentence boundary
            if end < len(text):
                sentence_end = self._find_sentence_boundary(text, end - 100, end + 100)
                if sentence_end != -1:
                    end = sentence_end
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk_hash = hashlib.md5(chunk_text.encode()).hexdigest()[:8]
                
                chunk = {
                    "chunk_id": f"chunk_{chunk_id}_{chunk_hash}",
                    "text": chunk_text,
                    "start_pos": start,
                    "end_pos": end,
                    "length": len(chunk_text),
                    "metadata": metadata or {}
                }
                
                clause_info = self._extract_clause_info(chunk_text)
                if clause_info:
                    chunk["clause_id"] = clause_info
                
                chunks.append(chunk)
                chunk_id += 1
            
            start = max(start + self.chunk_size - self.chunk_overlap, end)
            
            if start >= len(text):
                break
        
        logger.info(f"Created {len(chunks)} chunks from text of length {len(text)}")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """Find the best sentence boundary within range"""
        if start < 0:
            start = 0
        if end > len(text):
            end = len(text)
        
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        
        best_pos = -1
        for i in range(end - 1, start - 1, -1):
            for ending in sentence_endings:
                if text[i:i+len(ending)] == ending:
                    best_pos = i + 1
                    break
            if best_pos != -1:
                break
        
        return best_pos
    
    def _extract_clause_info(self, text: str) -> str:
        """Extract clause numbering from text if available"""
        patterns = [
            r'(?i)(?:clause|section|article)\s+(\d+(?:\.\d+)*)',
            r'(\d+(?:\.\d+)+)\s*[\.:|−]',
            r'^(\d+(?:\.\d+)+)',
            r'\((\d+(?:\.\d+)*)\)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text[:200])
            if match:
                return match.group(1)
        
        return None


class CloudDocumentRetriever:
    """MINIMAL VERSION - No vector search, basic keyword matching only"""
    
    def __init__(self):
        self.chunks = []
        self.chunker = DocumentChunker()
        logger.warning("🚨 MINIMAL MODE: Vector search disabled. Using basic keyword matching only.")
        logger.warning("🚨 For semantic search capabilities, upgrade to full deployment with ML dependencies.")
    
    def process_document(self, text: str, metadata: Dict, document_id: str = None) -> int:
        """Process document and store chunks for retrieval"""
        try:
            # Clear existing chunks for new document
            self.chunks = []
            
            # Chunk the document
            chunks = self.chunker.chunk_text(text, metadata)
            
            # Store chunks with document_id
            for chunk in chunks:
                chunk['document_id'] = document_id or 'default'
                self.chunks.append(chunk)
            
            logger.info(f"Processed document into {len(chunks)} chunks")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise
    
    def query(self, query_text: str, document_id: str = None, top_k: int = 5) -> List[Dict]:
        """Simple keyword-based retrieval - no semantic search"""
        try:
            if not self.chunks:
                logger.warning("No documents have been processed yet")
                return []
            
            # Filter by document_id if specified
            relevant_chunks = self.chunks
            if document_id:
                relevant_chunks = [chunk for chunk in self.chunks if chunk.get('document_id') == document_id]
            
            # Simple keyword matching
            query_words = set(query_text.lower().split())
            scored_chunks = []
            
            for chunk in relevant_chunks:
                chunk_text = chunk['text'].lower()
                
                # Count keyword matches
                matches = sum(1 for word in query_words if word in chunk_text)
                
                if matches > 0:
                    # Simple scoring: percentage of query words found
                    score = matches / len(query_words)
                    
                    scored_chunk = chunk.copy()
                    scored_chunk['similarity_score'] = score
                    scored_chunk['matches'] = matches
                    scored_chunks.append(scored_chunk)
            
            # Sort by score descending
            scored_chunks.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Return top_k results
            results = scored_chunks[:top_k]
            
            logger.info(f"Found {len(results)} relevant chunks using keyword matching")
            return results
            
        except Exception as e:
            logger.error(f"Error during retrieval: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics"""
        return {
            "total_chunks": len(self.chunks),
            "mode": "minimal",
            "search_type": "keyword_matching",
            "vector_search": False,
            "warning": "Running in minimal mode - no semantic search available"
        }
