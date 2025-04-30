# Build stage
FROM python:3.12-slim as builder

WORKDIR /app
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-dev --no-interaction --no-ansi

# Runtime stage
FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /app/.venv .venv
ENV PATH="/app/.venv/bin:$PATH"

COPY ./app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
