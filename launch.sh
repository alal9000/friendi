#!/bin/sh

# Wait for Redis to be available
echo "Waiting for Redis..."
until nc -z redis 6379; do
  sleep 1
done

echo "Redis is available. Starting Django-Q..."
python manage.py qcluster
