# Multi-stage Dockerfile for Chameleon-SRE
# Stage 1: Build environment (larger, includes compilation tools)
FROM python:3.10-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ============================================================================
# Stage 2: Runtime environment (smaller, production-ready)
FROM python:3.10-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    kubectl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app directory
WORKDIR /app

# Copy application code
COPY src/ /app/src/
COPY scripts/ /app/scripts/
COPY docs/ /app/docs/

# Create necessary directories
RUN mkdir -p /app/chroma_db /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV KUBECTL_PATH=/usr/bin/kubectl

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('${OLLAMA_BASE_URL}/api/tags')" || exit 1

# Default command (can be overridden)
CMD ["python", "src/main.py"]

# Labels
LABEL maintainer="Senior MLOps Architect"
LABEL version="1.0.0"
LABEL description="Chameleon-SRE: Autonomous Site Reliability Engineer"
