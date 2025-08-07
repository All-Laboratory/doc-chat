import os
import logging
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentReasoningDB:
    """MINIMAL VERSION - No PostgreSQL, basic in-memory logging only"""
    
    def __init__(self):
        logger.warning("🚨 MINIMAL MODE: Database features disabled to reduce image size.")
        logger.warning("🚨 All data will be lost when container restarts.")
        logger.warning("🚨 For persistent storage, upgrade to full deployment with PostgreSQL.")
        
        # In-memory storage for minimal functionality
        self.sessions = {}
        self.documents = {}
        self.queries = []
        self.connected = False  # Always False in minimal mode
    
    def is_connected(self) -> bool:
        """Check if database is connected - always False in minimal mode"""
        return False
    
    def log_document_upload(self, filename: str, file_size: int, metadata: Dict, session_id: str = None) -> Optional[str]:
        """Log document upload event - minimal in-memory version"""
        try:
            document_id = str(uuid.uuid4())
            
            self.documents[document_id] = {
                'id': document_id,
                'filename': filename,
                'file_size': file_size,
                'metadata': metadata,
                'session_id': session_id,
                'uploaded_at': datetime.now(timezone.utc).isoformat(),
                'status': 'uploaded'
            }
            
            logger.info(f"📝 MINIMAL: Logged document upload: {filename} (ID: {document_id})")
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to log document upload: {str(e)}")
            return None
    
    def log_query(self, query: str, response: Dict, document_id: str = None, 
                  session_id: str = None, processing_time: float = None, 
                  relevant_chunks: List[Dict] = None) -> Optional[str]:
        """Log query and response - minimal in-memory version"""
        try:
            query_id = str(uuid.uuid4())
            
            query_log = {
                'id': query_id,
                'query': query,
                'response': response,
                'document_id': document_id,
                'session_id': session_id,
                'processing_time_seconds': processing_time,
                'relevant_chunks_count': len(relevant_chunks) if relevant_chunks else 0,
                'relevant_chunks': relevant_chunks[:3] if relevant_chunks else [],  # Keep only first 3
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'decision': response.get('decision', 'unknown'),
                'confidence_score': 0.5
            }
            
            self.queries.append(query_log)
            
            # Keep only last 100 queries to avoid memory bloat
            if len(self.queries) > 100:
                self.queries = self.queries[-100:]
            
            logger.info(f"📝 MINIMAL: Logged query (ID: {query_id})")
            return query_id
            
        except Exception as e:
            logger.error(f"Failed to log query: {str(e)}")
            return None
    
    def create_session(self, user_agent: str = None, ip_address: str = None) -> Optional[str]:
        """Create a new session - minimal in-memory version"""
        try:
            session_id = str(uuid.uuid4())
            
            self.sessions[session_id] = {
                'id': session_id,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'user_agent': user_agent,
                'ip_address': ip_address,
                'queries_count': 0,
                'documents_count': 0,
                'last_activity': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"📝 MINIMAL: Created session (ID: {session_id})")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            return None
    
    def update_session_activity(self, session_id: str, query_count: int = 0, document_count: int = 0) -> bool:
        """Update session activity - minimal in-memory version"""
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session['queries_count'] += query_count
                session['documents_count'] += document_count
                session['last_activity'] = datetime.now(timezone.utc).isoformat()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to update session activity: {str(e)}")
            return False
    
    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """Get session statistics - minimal in-memory version"""
        try:
            if session_id in self.sessions:
                return self.sessions[session_id]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {str(e)}")
            return None
    
    def get_query_history(self, session_id: str = None, limit: int = 20) -> List[Dict]:
        """Get query history - minimal in-memory version"""
        try:
            filtered_queries = self.queries
            
            if session_id:
                filtered_queries = [q for q in self.queries if q.get('session_id') == session_id]
            
            # Return most recent queries
            return sorted(filtered_queries, key=lambda x: x['timestamp'], reverse=True)[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get query history: {str(e)}")
            return []
    
    def get_analytics_data(self) -> Dict[str, Any]:
        """Get analytics data - minimal in-memory version"""
        try:
            return {
                'total_sessions': len(self.sessions),
                'total_documents': len(self.documents),
                'total_queries': len(self.queries),
                'mode': 'minimal',
                'warning': 'In-memory data only, will be lost on restart'
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {str(e)}")
            return {'error': str(e)}
    
    def close(self):
        """Close database connection - no-op in minimal mode"""
        logger.info("📝 MINIMAL: No database connection to close")
        pass


# Create global instance
db = DocumentReasoningDB()
