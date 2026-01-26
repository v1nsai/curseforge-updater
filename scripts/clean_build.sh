#!/bin/bash

set -e

docker compose down
docker compose build --no-cache
docker compose up -d --force-recreate
docker compose logs -f