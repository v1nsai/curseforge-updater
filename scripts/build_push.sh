#!/bin/bash

set -e

APP_VERSION="$1"
if [ -z "$APP_VERSION" ]; then
    echo "Error: No app version provided."
    echo "Usage: $0 <app_version>"
    exit 1
fi

docker compose build --no-cache
docker tag doctor3w/curseforge-updater:latest doctor3w/curseforge-updater:"$APP_VERSION"
docker push doctor3w/curseforge-updater:"$APP_VERSION"