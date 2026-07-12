FROM python:3.11-slim AS builder

# Build arguments
ARG TARGETARCH
ARG TARGETPLATFORM

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements first (cache optimization)
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - Production image
FROM python:3.11-slim

# Build arguments
ARG APP_VERSION=0.1.0
ARG ENVIRONMENT=production
ARG BUILD_DATE
ARG VCS_REF

# Runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgomp1 \
    libssl3 \
    ca-certificates \
    tini \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r app && useradd -r -g app -m -d /home/app app

# Copy Python packages from builder
COPY --from=builder --chown=app:app /root/.local /home/app/.local

# Set PATH
ENV PATH=/home/app/.local/bin:$PATH

# Set working directory
WORKDIR /app
RUN chown -R app:app /app

# Copy application code
COPY --chown=app:app app/ ./app/
COPY --chown=app:app ml/ ./ml/
COPY --chown=app:app alembic/ ./alembic/
COPY --chown=app:app scripts/ ./scripts/
COPY --chown=app:app alembic.ini .
COPY --chown=app:app pyproject.toml .

# Copy environment file based on environment
COPY --chown=app:app .env.${ENVIRONMENT} .env

# Add wait-for-it script
COPY --chown=app:app scripts/wait-for-it.sh /usr/local/bin/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh

# Switch to non-root user
USER app

# Environment Configuration
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV APP_VERSION=${APP_VERSION}
ENV ENVIRONMENT=${ENVIRONMENT}

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Labels
LABEL maintainer="Data Science Team <team@kenyalend.co.ke>"
LABEL application="kenya-lend-intelligence"
LABEL version="${APP_VERSION}"
LABEL environment="${ENVIRONMENT}"
LABEL description="AI-Powered Customer Intelligence Platform for Kenyan Digital Lenders"
LABEL organization="KenyaLend"
LABEL build_date="${BUILD_DATE}"
LABEL vcs_ref="${VCS_REF}"
LABEL security.contact="security@kenyalend.co.ke"

# Runtime Configuration
EXPOSE 8000

# Use tini as init process for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Wait for database then start application
CMD ["sh", "-c", "wait-for-it.sh $DATABASE_HOST:$DATABASE_PORT -t 60 -- uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4"]