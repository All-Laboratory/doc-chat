# Use Python Alpine for smallest possible base image
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install minimal system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Copy requirements first for better caching
COPY requirements.txt .

# Create minimal requirements for Railway
RUN echo "# Minimal requirements for Railway deployment" > requirements.minimal.txt && \
    echo "fastapi>=0.104.1" >> requirements.minimal.txt && \
    echo "uvicorn>=0.24.0" >> requirements.minimal.txt && \
    echo "python-multipart>=0.0.6" >> requirements.minimal.txt && \
    echo "python-dotenv>=1.0.0" >> requirements.minimal.txt && \
    echo "requests>=2.31.0" >> requirements.minimal.txt && \
    echo "sentence-transformers>=2.2.2" >> requirements.minimal.txt && \
    echo "torch>=2.0.0 --index-url https://download.pytorch.org/whl/cpu" >> requirements.minimal.txt && \
    echo "pymupdf>=1.23.0" >> requirements.minimal.txt && \
    echo "python-docx>=0.8.11" >> requirements.minimal.txt && \
    echo "psycopg2-binary>=2.9.9" >> requirements.minimal.txt && \
    echo "pinecone>=7.3.0" >> requirements.minimal.txt && \
    echo "groq>=0.4.1" >> requirements.minimal.txt

# Install Python dependencies with maximum optimization
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.minimal.txt && \
    pip cache purge && \
    rm -rf ~/.cache/pip /tmp/* /var/tmp/* && \
    find /usr/local -name '*.pyc' -delete && \
    find /usr/local -name '__pycache__' -delete

# Copy only essential application files
COPY app/ ./app/
COPY start_server.py .

# Create non-root user and clean up
RUN adduser -D -s /bin/sh user && \
    chown -R user:user /app && \
    rm -rf /tmp/* /var/tmp/* requirements.txt requirements.minimal.txt

USER user

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["python", "start_server.py"]
