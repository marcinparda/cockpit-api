# Build stage
FROM python:3.12 AS builder

WORKDIR /app
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

RUN mkdir /opt/poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_HOME=/opt/poetry

ENV PATH="$POETRY_HOME/bin:${PATH}"

RUN apt -y update && apt -y install curl
RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=2.1.2 python3 -

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --only main --no-root --no-interaction --no-ansi

# Runtime stage
FROM python:3.12

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
