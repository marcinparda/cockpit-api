#!/bin/bash
set -e

# Function to check if PostgreSQL is ready
function postgres_ready() {
  python -c "
import sys
import psycopg2
import os

try:
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME', ''),
        user=os.environ.get('DB_USER', ''),
        password=os.environ.get('DB_PASSWORD', ''),
        host=os.environ.get('DB_HOST', ''),
        port=os.environ.get('DB_PORT', '')
    )
    conn.close()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
"
}

echo "Waiting for PostgreSQL to be ready..."
RETRIES=10
RETRY_INTERVAL=3
until postgres_ready || [ $RETRIES -eq 0 ]; do
  echo "Waiting for PostgreSQL server, $((RETRIES)) remaining attempts..."
  RETRIES=$((RETRIES-1))
  sleep $RETRY_INTERVAL
  RETRY_INTERVAL=$((RETRY_INTERVAL+2))
done

if [ $RETRIES -eq 0 ]; then
  echo "Failed to connect to PostgreSQL after multiple attempts. Exiting."
  exit 1
fi

echo "PostgreSQL is ready!"

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 80 --reload
