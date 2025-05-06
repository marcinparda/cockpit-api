#!/bin/bash
set -e

# Wait for the database to be ready
echo "Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "Database is ready!"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# If command is provided, execute it, otherwise start the application
if [ "$#" -gt 0 ]; then
  exec "$@"
else
  # Start the application with uvicorn
  echo "Starting the application..."
  exec uvicorn src.main:app --host 0.0.0.0 --port 8000
fi
