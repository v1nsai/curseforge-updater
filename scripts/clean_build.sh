#!/bin/bash

set -e

# check if $.services.curseforge-updater.build is defined and not commented out in docker-compose.yaml
if ! grep -q '^\s*#\s*build:' docker-compose.yaml; then
    echo "Building locally from Dockerfile..."
else
    echo "You probably want to uncomment the build section in docker-compose.yaml before running this script..."
    exit 1
fi
docker compose down
docker compose build --no-cache
docker compose up -d --force-recreate
docker compose logs -f --timestamps