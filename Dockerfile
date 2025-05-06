FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gcc libpq-dev curl && \
    pip install --upgrade pip && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Configure Poetry
ENV PATH="/root/.local/bin:$PATH" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# Copy dependencies first
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser

# Set Python environment
ENV PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy application code with proper permissions
COPY --chown=appuser:appuser . .

# Configure entrypoint
RUN chmod +x /app/entrypoint.sh
USER appuser
ENTRYPOINT ["/app/entrypoint.sh"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["/app/entrypoint.sh"]
