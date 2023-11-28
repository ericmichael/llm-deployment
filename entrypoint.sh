#!/bin/bash
set -e

if [ -z "$OPENAI_API_BASE" ]; then
    unset OPENAI_API_BASE
fi

exec "$@"