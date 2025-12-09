#!/bin/bash

echo "🚀 Starting OriginHub API..."

# Configuration
MAX_WAIT_TIME=${POSTGRES_MAX_WAIT_TIME:-60}  # Maximum wait time in seconds (default: 60)
WAIT_INTERVAL=2  # Check interval in seconds
ELAPSED_TIME=0

# Wait for PostgreSQL to be ready (with timeout)
echo "⏳ Waiting for PostgreSQL to be ready (max ${MAX_WAIT_TIME}s)..."
while [ $ELAPSED_TIME -lt $MAX_WAIT_TIME ]; do
  if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready!"
    POSTGRES_READY=true
    break
  fi
  echo "   PostgreSQL is unavailable - sleeping (${ELAPSED_TIME}s/${MAX_WAIT_TIME}s)"
  sleep $WAIT_INTERVAL
  ELAPSED_TIME=$((ELAPSED_TIME + WAIT_INTERVAL))
done

if [ "${POSTGRES_READY:-false}" != "true" ]; then
  echo "⚠️  WARNING: PostgreSQL is not available after ${MAX_WAIT_TIME}s"
  echo "⚠️  The application will start but database operations may fail"
  echo "⚠️  Check your database connection and restart if needed"
  POSTGRES_READY=false
fi

# Run database migrations (only if PostgreSQL is ready)
if [ "$POSTGRES_READY" = "true" ]; then
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
else
  echo "⏭️  Skipping migrations (PostgreSQL not available)"
fi

# Start the application (always start, even if DB is down)
echo "🎯 Starting FastAPI application..."
if [ "$POSTGRES_READY" != "true" ]; then
  echo "⚠️  Starting in degraded mode - database connectivity issues may occur"
fi
exec "$@"

