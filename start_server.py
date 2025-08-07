#!/usr/bin/env python3
"""
Startup script for HackRX API server
"""

import uvicorn
import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Also add the app directory
app_dir = os.path.join(current_dir, 'app')
if os.path.exists(app_dir):
    sys.path.insert(0, app_dir)
    
print(f"🔍 Current working directory: {os.getcwd()}")
print(f"🔍 Python path includes: {current_dir}")
print(f"🔍 App directory: {app_dir}")

if __name__ == "__main__":
    print("🚀 Starting HackRX API Server...")
    print("📍 URL: http://localhost:8000")
    print("🔧 Endpoints:")
    print("   - POST /hackrx/run")
    print("   - POST /api/v1/hackrx/run")
    print("   - GET /health")
    print("   - GET /docs (API documentation)")
    print("\n" + "="*50)
    print("Press Ctrl+C to stop the server")
    print("="*50 + "\n")
    
    try:
        # Get port from Railway environment or default to 8000
        port = int(os.getenv("PORT", 8000))
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            reload=False,  # Disable reload for Railway deployment
            log_level="info",
            workers=1  # Single worker for Railway
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
