# Multi-stage Dockerfile for USDT/KRW Crypto Trading Bot
# Optimized for production deployment with security and size considerations

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add metadata
LABEL maintainer="teder-bot@crypto.local" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="teder-crypto-bot" \
      org.label-schema.description="24/7 USDT/KRW Automated Trading Bot" \
      org.label-schema.url="https://github.com/your-repo/teder" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim as production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r teder && useradd -r -g teder -s /bin/false teder

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/config && \
    chown -R teder:teder /app

# Copy application code
COPY --chown=teder:teder . .

# Set timezone to Asia/Seoul for Korean market hours
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create health check script
RUN echo '#!/bin/bash\n\
python -c "import sys, os; sys.path.append(\"/app\"); \n\
try: \n\
    from src.api.coinone_client import CoinoneClient; \n\
    client = CoinoneClient(); \n\
    result = client.get_ticker(\"usdt\"); \n\
    sys.exit(0 if result and result.get(\"result\") == \"success\" else 1) \n\
except Exception as e: \n\
    print(f\"Health check failed: {e}\"); \n\
    sys.exit(1)"' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ["/app/healthcheck.sh"]

# Switch to non-root user
USER teder

# Expose port for monitoring (optional)
EXPOSE 8080

# Set default command
CMD ["python", "main_live.py"]