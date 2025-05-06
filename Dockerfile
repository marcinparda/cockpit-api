# Build stage
FROM python:3.12-slim AS builder

# Set environment variables for Poetry
ENV POETRY_VERSION=2.1.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install Poetry using pip (official recommended way for Docker)
RUN pip install "poetry==$POETRY_VERSION" --no-cache-dir

WORKDIR /app

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Install curl for healthcheck and required dependencies for psycopg2
RUN apt-get update && apt-get install -y curl libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy virtual environment from builder
COPY --from=builder /app/.venv .venv

# Copy application code - updating to copy from project root instead of assuming ./app directory
COPY . .

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Add health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Use entrypoint script to run migrations before starting the app
CMD ["/app/entrypoint.sh"]
