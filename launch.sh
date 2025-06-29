#!/bin/sh

# Use the REDIS_HOST environment variable, or default to "redis"
REDIS_HOST=${REDIS_HOST:-redis}

# Print the Redis host for debugging
echo "Using Redis host: $REDIS_HOST"
echo "Waiting for Redis at $REDIS_HOST:6379..."

# Wait for Redis to be available
until nc -z "$REDIS_HOST" 6379; do
  echo "Still waiting for Redis at $REDIS_HOST..."
  sleep 1
done

echo "Redis is available. Starting Django-Q..."
python manage.py qcluster
