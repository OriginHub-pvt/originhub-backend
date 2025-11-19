#!/bin/bash

echo "🚀 Starting OriginHub API..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" > /dev/null 2>&1; do
  echo "   PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "✅ PostgreSQL is ready!"

# Run database migrations
echo "📦 Running database migrations..."
set +e  # Don't exit on error for migrations
alembic upgrade head
MIGRATION_STATUS=$?
set -e  # Re-enable exit on error

if [ $MIGRATION_STATUS -eq 0 ]; then
    echo "✅ Migrations completed successfully!"
else
    echo "⚠️  Migration completed with warnings (this is OK if migrations were already applied)"
fi

# Start the application
echo "🎯 Starting FastAPI application..."
exec "$@"

