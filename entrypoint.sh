#!/bin/bash
set -e

if [ -z "$OPENAI_API_BASE" ]; then
    unset OPENAI_API_BASE
fi

# Install Node dependencies
npm install

# Run the Webpacker build
npm run build

# Run Django migrations
python manage.py migrate

# Run Django static file collection
python manage.py collectstatic --noinput

exec "$@"