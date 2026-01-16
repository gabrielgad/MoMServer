#!/bin/bash
# Build and optionally push the TGE builder image
# Usage: ./scripts/build-tge.sh [--push] [VERSION]
# Example: ./scripts/build-tge.sh --push v1.0

set -e

REGISTRY="10.0.0.6:5000"
VERSION="${2:-v1.0}"
TGE_IMAGE="$REGISTRY/momserver/tge-builder:$VERSION"
TMPFS="/dev/shm/tge-build"

echo "Building TGE image..."
echo "Image: $TGE_IMAGE"
echo "Using tmpfs at: $TMPFS"

# Use tmpfs for faster I/O during compilation
rm -rf "$TMPFS" && mkdir -p "$TMPFS/tge-152-fork"

# Copy only what's needed for TGE build
cp -r tge-152-fork/{engine,lib,mk,Makefile} "$TMPFS/tge-152-fork/"
cp Dockerfile.tge-builder "$TMPFS/"

BUILDAH_FORMAT=docker podman build --layers --memory=8g \
    --tls-verify=false \
    --build-arg BASE_IMAGE="$REGISTRY/momserver/base-deps:buster-i386" \
    -f Dockerfile.tge-builder \
    -t "$TGE_IMAGE" \
    "$TMPFS"

# Cleanup tmpfs
rm -rf "$TMPFS"

if [[ "$1" == "--push" ]]; then
    echo "Pushing to registry..."
    podman push "$TGE_IMAGE" --tls-verify=false
fi

echo "Done: $TGE_IMAGE"
