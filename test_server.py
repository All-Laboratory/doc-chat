#!/usr/bin/env python3
"""
Simple test server to verify Railway deployment works
"""
from fastapi import FastAPI
import os

app = FastAPI(title="Railway Test Server", version="1.0.0")

@app.get("/")
async def root():
    return {
        "message": "🚀 Railway deployment successful!",
        "status": "healthy", 
        "python_version": "3.11",
        "port": os.getenv("PORT", 8000)
    }

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Server is running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
