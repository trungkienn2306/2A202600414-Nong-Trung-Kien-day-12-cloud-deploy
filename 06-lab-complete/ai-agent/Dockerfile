# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt
# Add specific redis checkpoint and openai fallback dependencies
RUN pip install --no-cache-dir --user langgraph-checkpoint-redis pydantic-settings langchain-openai redis

# Stage 2: Production
FROM python:3.12-slim

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-privileged user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY . ./

# Environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Correct permissions
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api_main:app", "--host", "0.0.0.0", "--port", "8000"]
