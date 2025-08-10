import os
import logging
import requests
from typing import Dict, List
from urllib.parse import urlparse

# Try importing PDF libraries with fallbacks
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentExtractor:
    """Extract text from various document formats - Railway optimized"""
    
    def __init__(self):
        self.supported_formats = {".txt"}
        
        if PYMUPDF_AVAILABLE:
            self.supported_formats.add(".pdf")
            logger.info("✅ PyMuPDF available - PDF support enabled")
        elif PYPDF2_AVAILABLE:
            self.supported_formats.add(".pdf")
            logger.info("✅ PyPDF2 available - PDF support enabled (fallback)")
        else:
            logger.warning("⚠️ No PDF library available - PDF support disabled")
            
        if DOCX_AVAILABLE:
            self.supported_formats.add(".docx")
            logger.info("✅ python-docx available - DOCX support enabled")
        else:
            logger.warning("⚠️ python-docx not available - DOCX support disabled")
    
    def detect_file_type_from_url(self, url: str) -> str:
        """Detect file type from URL"""
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        if "pdf" in path or "pdf" in url.lower():
            return ".pdf"
        elif "docx" in path or "word" in path:
            return ".docx"
        elif "doc" in path:
            return ".docx"  # Treat as docx for processing
        else:
            return ".pdf"  # Default to PDF
    
    def extract_text(self, file_path: str) -> Dict[str, any]:
        """Extract text from document based on file extension"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: {self.supported_formats}")
        
        try:
            if file_ext == ".pdf":
                return self._extract_pdf(file_path)
            elif file_ext == ".docx":
                return self._extract_docx(file_path)
            elif file_ext == ".txt":
                return self._extract_txt(file_path)
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise
    
    def _extract_pdf(self, file_path: str) -> Dict[str, any]:
        """Extract text from PDF using available library"""
        if PYMUPDF_AVAILABLE:
            return self._extract_pdf_pymupdf(file_path)
        elif PYPDF2_AVAILABLE:
            return self._extract_pdf_pypdf2(file_path)
        else:
            raise ValueError("No PDF processing library available")
    
    def _extract_pdf_pymupdf(self, file_path: str) -> Dict[str, any]:
        """Extract text from PDF using PyMuPDF"""
        doc = fitz.open(file_path)
        text_content = []
        metadata = {
            "total_pages": len(doc),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "file_type": "pdf",
            "processor": "pymupdf"
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            if page_text.strip():  # Only add non-empty pages
                text_content.append({
                    "page_number": page_num + 1,
                    "text": page_text
                })
        
        doc.close()
        
        # Combine all text
        full_text = "\n\n".join([page["text"] for page in text_content])
        
        return {
            "text": full_text,
            "pages": text_content,
            "metadata": metadata
        }
    
    def _extract_pdf_pypdf2(self, file_path: str) -> Dict[str, any]:
        """Extract text from PDF using PyPDF2 (fallback)"""
        text_content = []
        full_text_parts = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                
                if page_text.strip():  # Only add non-empty pages
                    text_content.append({
                        "page_number": page_num + 1,
                        "text": page_text
                    })
                    full_text_parts.append(page_text)
        
        full_text = "\n\n".join(full_text_parts)
        
        metadata = {
            "total_pages": total_pages,
            "title": "",
            "author": "",
            "file_type": "pdf",
            "processor": "pypdf2"
        }
        
        return {
            "text": full_text,
            "pages": text_content,
            "metadata": metadata
        }
    
    def _extract_docx(self, file_path: str) -> Dict[str, any]:
        """Extract text from DOCX using python-docx"""
        if not DOCX_AVAILABLE:
            raise ValueError("python-docx not available")
            
        doc = docx.Document(file_path)
        
        paragraphs = []
        full_text_parts = []
        
        for i, paragraph in enumerate(doc.paragraphs):
            if paragraph.text.strip():
                paragraphs.append({
                    "paragraph_number": i + 1,
                    "text": paragraph.text
                })
                full_text_parts.append(paragraph.text)
        
        full_text = "\n\n".join(full_text_parts)
        
        # Extract basic metadata
        try:
            core_props = doc.core_properties
            metadata = {
                "title": core_props.title or "",
                "author": core_props.author or "",
                "total_paragraphs": len(paragraphs),
                "file_type": "docx"
            }
        except:
            metadata = {
                "title": "",
                "author": "",
                "total_paragraphs": len(paragraphs),
                "file_type": "docx"
            }
        
        return {
            "text": full_text,
            "paragraphs": paragraphs,
            "metadata": metadata
        }
    
    def _extract_txt(self, file_path: str) -> Dict[str, any]:
        """Extract text from plain text file"""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1
                with open(file_path, 'r', encoding='latin-1') as file:
                    content = file.read()
                logger.warning("File read using latin-1 encoding")
            except Exception as e:
                raise ValueError(f"Cannot read file as text: {str(e)}")
        
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        metadata = {
            "total_lines": len(lines),
            "non_empty_lines": len(non_empty_lines),
            "file_type": "txt"
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
