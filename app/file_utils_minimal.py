import os
import logging
import requests
from typing import Dict, List
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentExtractor:
    """Extract text from various document formats - MINIMAL VERSION"""
    
    def __init__(self):
        # Only support text files in minimal mode
        self.supported_formats = {".txt"}
        logger.warning("🚨 MINIMAL MODE: Only .txt files supported. PDF/DOCX support disabled to reduce image size.")
    
    def detect_file_type_from_url(self, url: str) -> str:
        """Detect file type from URL - always returns .txt in minimal mode"""
        logger.warning("🚨 MINIMAL MODE: All documents will be treated as plain text")
        return ".txt"
    
    def extract_text(self, file_path: str) -> Dict[str, any]:
        """Extract text from document - only supports .txt in minimal mode"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # In minimal mode, try to read any file as plain text
        try:
            return self._extract_txt(file_path)
        except Exception as e:
            # If file is binary (PDF/DOCX), return error message
            logger.error(f"Cannot process binary file in minimal mode: {str(e)}")
            raise ValueError(
                "🚨 MINIMAL MODE: Cannot process PDF/DOCX files. "
                "This deployment uses minimal dependencies for size optimization. "
                "Only plain text files are supported. "
                "Please provide documents as .txt files or upgrade to full deployment."
            )
    
    def _extract_txt(self, file_path: str) -> Dict[str, any]:
        """Extract text from plain text file"""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1 for binary files
                with open(file_path, 'r', encoding='latin-1') as file:
                    content = file.read()
                logger.warning("File read using latin-1 encoding - may not be optimal for text extraction")
            except Exception as e:
                raise ValueError(f"Cannot read file as text: {str(e)}")
        
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        metadata = {
            "total_lines": len(lines),
            "non_empty_lines": len(non_empty_lines),
            "file_type": "txt",
            "mode": "minimal"
        }
        
        return {
            "text": content,
            "lines": lines,
            "metadata": metadata
        }
    
    def validate_document(self, file_path: str) -> bool:
        """Validate if document can be processed"""
        try:
            result = self.extract_text(file_path)
            return len(result["text"].strip()) > 0
        except Exception as e:
            logger.error(f"Document validation failed: {str(e)}")
            return False
