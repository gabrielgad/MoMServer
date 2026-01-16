#!/bin/bash
# Build and optionally push the base dependencies image
# Usage: ./scripts/build-base.sh [--push]

set -e

REGISTRY="10.0.0.6:5000"
IMAGE="$REGISTRY/momserver/base-deps:buster-i386"

echo "Building base dependencies image..."
echo "Image: $IMAGE"

BUILDAH_FORMAT=docker podman build --layers \
    -f Dockerfile.base-deps \
    -t "$IMAGE" \
    .

if [[ "$1" == "--push" ]]; then
    echo "Pushing to registry..."
    podman push "$IMAGE" --tls-verify=false
fi

echo "Done: $IMAGE"
