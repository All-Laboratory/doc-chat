import os
import time
import tempfile
import logging
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uuid

# Import our modules
try:
    from app.file_utils import DocumentExtractor
    from app.llm_utils_groq_first import DocumentReasoningLLM
    from app.db import db
except ImportError:
    from file_utils import DocumentExtractor
    from llm_utils_groq_first import DocumentReasoningLLM
    from db import db

try:
    try:
        from app.vector_retriever import CloudDocumentRetriever
        CLOUD_RETRIEVER_AVAILABLE = True
    except ImportError:
        from vector_retriever import CloudDocumentRetriever
        CLOUD_RETRIEVER_AVAILABLE = True
except ImportError as e:
    CLOUD_RETRIEVER_AVAILABLE = False
    print(f"Cloud retriever not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
document_extractor = None
document_retriever = None
llm_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events with timeout handling for Railway"""
    # Startup
    global document_extractor, document_retriever, llm_engine
    
    logger.info("🚀 Starting Document Reasoning Assistant...")
    start_time = time.time()
    
    try:
        # Initialize document extractor first (fast)
        logger.info("📄 Initializing Document Extractor...")
        document_extractor = DocumentExtractor()
        logger.info("✅ Document Extractor initialized")
        
        # Check if we're in minimal mode
        if not CLOUD_RETRIEVER_AVAILABLE:
            logger.warning("🚨 MINIMAL MODE: Running without vector search capabilities")
            logger.warning("🚨 Only basic keyword matching will be available")
        
        # In minimal mode, don't require Pinecone API key
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if not pinecone_api_key and CLOUD_RETRIEVER_AVAILABLE:
            logger.warning("⚠️ PINECONE_API_KEY not set - running in basic mode")
        
        # Check PostgreSQL connection (optional)
        logger.info("🗄️ Checking database connection...")
        if not db.is_connected():
            logger.warning("⚠️ PostgreSQL database not connected. Some features may not work properly.")
        else:
            logger.info("✅ Database connected")
        
        # Initialize Cloud Document Retriever (this loads the embedding model)
        logger.info("🧠 Initializing Cloud Document Retriever (Embedding Model + Pinecone)...")
        logger.info("📥 This may take a moment to download the embedding model...")
        
        try:
            document_retriever = CloudDocumentRetriever()
            logger.info("✅ Cloud Document Retriever initialized successfully")
        except Exception as retriever_error:
            logger.error(f"❌ Failed to initialize document retriever: {str(retriever_error)}")
            # Try to provide a fallback or better error message
            raise RuntimeError(f"Document retriever initialization failed: {str(retriever_error)}")
        
        # Initialize LLM engine
        logger.info("🤖 Initializing LLM Engine...")
        llm_engine = DocumentReasoningLLM()
        logger.info("✅ LLM Engine initialized")
        
        initialization_time = time.time() - start_time
        logger.info(f"🎉 All components initialized successfully in {initialization_time:.2f}s")
        logger.info("🌐 Application is ready to serve requests!")
        
    except Exception as e:
        initialization_time = time.time() - start_time
        logger.error(f"❌ Failed to initialize components after {initialization_time:.2f}s: {str(e)}")
        logger.error("💡 Tip: If using a large embedding model, try setting EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Document Reasoning Assistant...")
    if db.is_connected():
        db.close()

# Create FastAPI app
app = FastAPI(
    title="Document Reasoning Assistant",
    description="RAG-based document analysis and reasoning system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    direct_answer: str
    decision: str
    justification: str
    referenced_clauses: List[Dict[str, Any]]
    additional_info: str
    processing_time: float
    query_id: Optional[str] = None
    retrieval_stats: Dict[str, Any]

class DocumentStatus(BaseModel):
    uploaded: bool
    filename: Optional[str] = None
    chunks_count: int = 0
    document_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

# Hackathon-specific models
class HackathonRequest(BaseModel):
    documents: str  # URL to the document
    questions: List[str]

class HackathonResponse(BaseModel):
    answers: List[str]

# Hackathon endpoint
@app.post("/hackrx/run", response_model=HackathonResponse)
async def hackathon_process(request: HackathonRequest, req: Request):
    """Process document from URL and answer questions"""
    
    # Check authentication
    auth_header = req.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized: Missing or invalid Authorization header")
    
    token = auth_header.split(" ")[1]
    if token != "6be388e87eae07a6e1ee672992bc2a22f207bbc7ff7e043758105f7d1fa45ffd":
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid token")

    # Download document
    try:
        response = requests.get(request.documents)
        response.raise_for_status()

        # Create a temporary file for the document
        file_suffix = document_extractor.detect_file_type_from_url(request.documents)
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        # Extract text
        logger.info("Extracting text from document URL...")
        extraction_result = document_extractor.extract_text(temp_file_path)

        # Process document
        document_id = str(uuid.uuid4())
        document_retriever.process_document(extraction_result["text"], extraction_result["metadata"], document_id)
        
        # Skip unnecessary wait time for better performance
        logger.info("Document processed and ready for querying")

        # Remove temporary file
        os.unlink(temp_file_path)

    except Exception as e:
        logger.error(f"Failed to process document from URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

    # Answer questions with improved error handling and timeout management
    answers = []
    for i, question in enumerate(request.questions):
        try:
            # Add 5-second delay between questions (except for the first one)
            if i > 0:
                logger.info(f"⏳ Waiting 5 seconds before processing next question to avoid rate limiting...")
                time.sleep(5)
            
            # Use the same document_id for retrieval that was used for processing
            logger.info(f"Processing question {i+1}/{len(request.questions)}: {question[:50]}...")
            relevant_chunks = document_retriever.query(question, document_id=document_id)
            
            if relevant_chunks:
                logger.info(f"Found {len(relevant_chunks)} relevant chunks for question")
                llm_response = llm_engine.analyze_document_query(question, relevant_chunks)
                
                # Extract direct answer from LLM response
                if isinstance(llm_response, dict) and "direct_answer" in llm_response:
                    answer = llm_response["direct_answer"]
                    logger.info(f"✅ Extracted answer: {answer[:100]}...")
                elif isinstance(llm_response, dict):
                    # Try to extract any useful response
                    answer = llm_response.get("justification", str(llm_response))
                    logger.warning("⚠️ No direct_answer field, using justification")
                else:
                    answer = str(llm_response) if llm_response else "Could not generate response."
                    logger.warning("⚠️ Unexpected response format")
            else:
                logger.warning(f"No relevant chunks found for question: {question}")
                answer = "No relevant information found in the document."
                
        except Exception as e:
            logger.error(f"Error processing question '{question}': {str(e)}")
            answer = f"Error processing question: {str(e)[:100]}..."
            
        answers.append(answer)
        logger.info(f"Answer {i+1} generated: {answer[:100]}...")

    logger.info(f"All {len(answers)} questions processed successfully")
    return HackathonResponse(answers=answers)

# API v1 endpoint (alias for hackrx endpoint)
@app.post("/api/v1/hackrx/run", response_model=HackathonResponse)
async def hackathon_process_v1(request: HackathonRequest, req: Request):
    """API v1 endpoint for hackathon - alias for /hackrx/run"""
    return await hackathon_process(request, req)

# Routes

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Document Reasoning Assistant API",
        "version": "1.0.0",
        "mode": "minimal" if not CLOUD_RETRIEVER_AVAILABLE else "full",
        "endpoints": {
            "hackrx": "/hackrx/run",
            "hackrx_v1": "/api/v1/hackrx/run",
            "health": "/health",
            "environment": "/env",
            "test": "/test",
            "stats": "/stats",
            "provider_status": "/provider-status",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with enhanced system information"""
    import platform
    import psutil
    from datetime import datetime
    
    def is_json_serializable(obj):
        """Check if object is JSON serializable"""
        try:
            import json
            json.dumps(obj)
            return True
        except (TypeError, ValueError):
            return False
    
    def clean_dict(d):
        """Recursively clean dictionary of non-serializable objects"""
        if not isinstance(d, dict):
            return str(d) if not is_json_serializable(d) else d
        
        cleaned = {}
        for k, v in d.items():
            if isinstance(v, dict):
                cleaned[k] = clean_dict(v)
            elif isinstance(v, (list, tuple)):
                cleaned[k] = [clean_dict(item) if isinstance(item, dict) else (str(item) if not is_json_serializable(item) else item) for item in v]
            elif is_json_serializable(v):
                cleaned[k] = v
            else:
                cleaned[k] = str(type(v).__name__)
        return cleaned
    
    # Get stats safely
    stats = {}
    if document_retriever:
        try:
            raw_stats = document_retriever.get_stats()
            stats = clean_dict(raw_stats)
        except Exception as e:
            stats = {"error": f"Failed to get stats: {str(e)}"}
    
    # Get system information
    system_info = {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "document_extractor": document_extractor is not None,
            "document_retriever": document_retriever is not None,
            "llm_engine": llm_engine is not None,
            "database": db.is_connected(),
            "cloud_retriever_available": CLOUD_RETRIEVER_AVAILABLE
        },
        "system": system_info,
        "stats": stats
    }

@app.post("/upload", response_model=DocumentStatus)
async def upload_document(request: Request, file: UploadFile = File(...), session_id: Optional[str] = Form(None)):
    """Upload and process document"""
    
    if not document_extractor or not document_retriever:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_ext}. Supported types: PDF, DOCX, TXT"
        )
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Extract text
        logger.info(f"Processing uploaded file: {file.filename}")
        extraction_result = document_extractor.extract_text(temp_file_path)
        
        # Process with retriever
        chunks_count = document_retriever.process_document(
            extraction_result["text"], 
            extraction_result["metadata"]
        )
        
        # Log to database
        document_id = None
        if db.is_connected():
            document_id = db.log_document_upload(
                filename=file.filename,
                file_size=len(content),
                metadata=extraction_result["metadata"],
                session_id=session_id
            )
            
            if session_id:
                db.update_session_activity(session_id, document_count=1)
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        logger.info(f"Document processed successfully: {file.filename} ({chunks_count} chunks)")
        
        return DocumentStatus(
            uploaded=True,
            filename=file.filename,
            chunks_count=chunks_count,
            document_id=document_id,
            metadata=extraction_result["metadata"]
        )
        
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Ask a question about the uploaded document"""
    
    if not document_retriever or not llm_engine:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Check if document is loaded
    stats = document_retriever.get_stats()
    if stats["total_chunks"] == 0:
        raise HTTPException(status_code=400, detail="No document uploaded. Please upload a document first.")
    
    start_time = time.time()
    
    try:
        # Retrieve relevant chunks
        logger.info(f"Processing query: {request.query[:100]}...")
        relevant_chunks = document_retriever.query(request.query)
        
        if not relevant_chunks:
            raise HTTPException(status_code=404, detail="No relevant information found in the document")
        
        # Generate LLM response
        llm_response = llm_engine.analyze_document_query(request.query, relevant_chunks)
        
        processing_time = time.time() - start_time
        
        # Log query to database
        query_id = None
        if db.is_connected():
            query_id = db.log_query(
                query=request.query,
                response=llm_response,
                session_id=request.session_id,
                processing_time=processing_time,
                relevant_chunks=relevant_chunks
            )
            
            if request.session_id:
                db.update_session_activity(request.session_id, query_count=1)
        
        # Prepare response
        response = QueryResponse(
            direct_answer=llm_response.get("direct_answer", "Unable to provide a direct answer."),
            decision=llm_response["decision"],
            justification=llm_response["justification"],
            referenced_clauses=llm_response["referenced_clauses"],
            additional_info=llm_response.get("additional_info", ""),
            processing_time=processing_time,
            query_id=query_id,
            retrieval_stats={
                "chunks_retrieved": len(relevant_chunks),
                "top_similarity_score": relevant_chunks[0]["similarity_score"] if relevant_chunks else 0,
                "total_chunks_available": stats["total_chunks"]
            }
        )
        
        logger.info(f"Query processed successfully in {processing_time:.2f}s: {llm_response['decision']}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@app.post("/session")
async def create_session(request: Request):
    """Create a new session"""
    user_agent = request.headers.get("user-agent")
    # Note: In production, implement proper IP detection
    ip_address = request.client.host if request.client else None
    
    session_id = None
    if db.is_connected():
        session_id = db.create_session(user_agent=user_agent, ip_address=ip_address)
    
    return {
        "session_id": session_id,
        "created": session_id is not None
    }

@app.get("/session/{session_id}/stats")
async def get_session_stats(session_id: str):
    """Get session statistics"""
    if not db.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")
    
    stats = db.get_session_stats(session_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return stats

@app.get("/history")
async def get_query_history(session_id: Optional[str] = None, limit: int = 20):
    """Get query history"""
    if not db.is_connected():
        return {"history": [], "message": "Database not available"}
    
    history = db.get_query_history(session_id=session_id, limit=min(limit, 100))
    return {"history": history}

@app.get("/stats")
async def get_system_stats():
    """Get system statistics"""
    # Get stats safely without threading objects
    retriever_stats = {}
    if document_retriever:
        try:
            raw_stats = document_retriever.get_stats()
            retriever_stats = {
                k: v for k, v in raw_stats.items() 
                if isinstance(v, (int, float, str, bool, list, dict, type(None)))
            }
        except Exception as e:
            retriever_stats = {"error": f"Failed to get stats: {str(e)}"}
    
    analytics = {}
    if db.is_connected():
        try:
            analytics = db.get_analytics_data()
        except Exception as e:
            analytics = {"error": f"Failed to get analytics: {str(e)}"}
    
    return {
        "retriever": retriever_stats,
        "analytics": analytics,
        "system": {
            "components_loaded": {
                "document_extractor": document_extractor is not None,
                "document_retriever": document_retriever is not None,
                "llm_engine": llm_engine is not None,
                "database": db.is_connected()
            }
        }
    }

@app.get("/env")
async def environment_info():
    """Get environment configuration information"""
    from datetime import datetime
    
    env_vars = {
        "PORT": os.getenv("PORT", "8000"),
        "PINECONE_API_KEY": "Set" if os.getenv("PINECONE_API_KEY") else "Not set",
        "GROQ_API_KEY": "Set" if os.getenv("GROQ_API_KEY") else "Not set",
        "DATABASE_URL": "Set" if os.getenv("DATABASE_URL") else "Not set",
        "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "Not Railway"),
        "NODE_ENV": os.getenv("NODE_ENV", "Not set")
    }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "environment": env_vars,
        "cloud_retriever_available": CLOUD_RETRIEVER_AVAILABLE,
        "mode": "minimal" if not CLOUD_RETRIEVER_AVAILABLE else "full"
    }

@app.get("/provider-status")
async def get_provider_status():
    """Get current status of LLM providers"""
    if not llm_engine:
        raise HTTPException(status_code=500, detail="LLM engine not initialized")
    
    try:
        provider_status = llm_engine.get_provider_status()
        return {
            "timestamp": time.time(),
            "strategy": "Groq-first with Together AI fallback",
            "providers": provider_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provider status: {str(e)}")

@app.get("/test")
async def test_system():
    """Test system components"""
    tests = {}
    
    # Test document extractor
    try:
        if document_extractor:
            tests["document_extractor"] = "OK"
        else:
            tests["document_extractor"] = "Not initialized"
    except Exception as e:
        tests["document_extractor"] = f"Error: {str(e)}"
    
    # Test document retriever
    try:
        if document_retriever:
            stats = document_retriever.get_stats()
            tests["document_retriever"] = f"OK - {stats}"
        else:
            tests["document_retriever"] = "Not initialized"
    except Exception as e:
        tests["document_retriever"] = f"Error: {str(e)}"
    
    # Test LLM engine
    try:
        if llm_engine:
            tests["llm_engine"] = "OK"
        else:
            tests["llm_engine"] = "Not initialized"
    except Exception as e:
        tests["llm_engine"] = f"Error: {str(e)}"
    
    # Test database
    try:
        if db.is_connected():
            tests["database"] = "Connected"
        else:
            tests["database"] = "Not connected (optional)"
    except Exception as e:
        tests["database"] = f"Error: {str(e)}"
    
    return {"tests": tests}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
