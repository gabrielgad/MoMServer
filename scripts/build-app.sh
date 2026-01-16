#!/bin/bash
# Build and optionally push the application image (fast - < 2 min)
# Usage: ./scripts/build-app.sh [--push] [TAG]
# Example: ./scripts/build-app.sh --push latest

set -e

REGISTRY="10.0.0.6:5000"
TAG="${2:-latest}"
APP_IMAGE="$REGISTRY/momserver/app:$TAG"

echo "Building application image..."
echo "Image: $APP_IMAGE"

# Use the app-specific dockerignore for minimal context
BUILDAH_FORMAT=docker podman build --layers \
    --tls-verify=false \
    --build-arg TGE_IMAGE="$REGISTRY/momserver/tge-builder:v1.0" \
    --ignorefile .dockerignore.app \
    -f Dockerfile.app \
    -t "$APP_IMAGE" \
    .

if [[ "$1" == "--push" ]]; then
    echo "Pushing to registry..."
    podman push "$APP_IMAGE" --tls-verify=false
fi

echo "Done: $APP_IMAGE (< 2 min for code changes)"
