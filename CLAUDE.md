# MoM Server - Development Guide

## Build System Overview

This project uses a three-tier Docker image strategy to optimize build times:

```
                    Zot Registry (10.0.0.6:5000)
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   [base-deps]          [tge-builder]         [app]
   i386/debian:buster   Pre-compiled libs     Application
   + apt + Python       + pytge.so            + Python code
   (~500MB, monthly)    (~800MB, rare)        (~15MB, daily)
```

### Build Times

| Scenario | Time |
|----------|------|
| Cold build (first time) | 40-90 min |
| TGE engine changes | 40-90 min (rare) |
| Python code changes | < 2 min |
| Config changes | < 1 min |

## Quick Start

### Running the Server

```bash
# Pull and run from registry
podman-compose -f docker-compose.tmpfs.yml up -d

# View logs
podman logs -f mom-server
```

### Development Workflow

After changing Python code:
```bash
./scripts/build-app.sh --push
podman-compose -f docker-compose.tmpfs.yml up -d
```

## Docker Images

### Image Hierarchy

| Image | Tag | Rebuild When |
|-------|-----|--------------|
| `momserver/base-deps` | `buster-i386` | System deps change (monthly) |
| `momserver/tge-builder` | `v1.0` | TGE engine code changes (rare) |
| `momserver/app` | `latest` | Python/config changes (daily) |

### Registry

- **Internal**: `10.0.0.6:5000`
- **External**: `registry.gabeforge.com`
- **Auth**: See `~/ssh-workspace/CLAUDE.md` for credentials

## Build Scripts

### `./scripts/build-app.sh [--push] [TAG]`
Fast build for Python/config changes. Default tag: `latest`
```bash
./scripts/build-app.sh --push           # Build and push :latest
./scripts/build-app.sh --push v2.0      # Build and push :v2.0
```

### `./scripts/build-tge.sh [--push] [VERSION]`
Rebuild TGE engine (40-90 min). Only needed when engine code changes.
```bash
./scripts/build-tge.sh --push v1.1      # New TGE version
```

### `./scripts/build-base.sh [--push]`
Rebuild base dependencies. Only needed when system packages change.
```bash
./scripts/build-base.sh --push
```

## Dockerfiles

| File | Purpose |
|------|---------|
| `Dockerfile.base-deps` | System packages + Python dependencies |
| `Dockerfile.tge-builder` | Compiles TGE engine and pytge.so |
| `Dockerfile.app` | Application layer (fast builds) |
| `Dockerfile.32bit` | Legacy monolithic build (reference) |

## GitHub Actions

The workflow at `.github/workflows/docker-images.yml` handles:

- **Auto build**: `app` image on push to master/main
- **Manual dispatch**: Any image via workflow_dispatch

### Secrets Required
- `REGISTRY_USER`: Registry username
- `REGISTRY_PASS`: Registry password

## Architecture Notes

### Why 32-bit?
TGE 1.5.2 is a 32-bit engine. The `pytge.so` Python extension must be compiled in a native 32-bit environment to avoid pointer truncation issues.

### Key Files
- `pytge.so` - Python bindings to Torque Game Engine
- `zoneserver.py` - Zone server implementation
- `mud/` - Game logic and world simulation
- `common/` - Shared TorqueScript code

### Ports
| Port | Service |
|------|---------|
| 2002-2003 | Master Server |
| 7000-7001 | World Server |
| 28000-28100 | Zone Servers |
| 8192 | Admin (Manhole) |

## Troubleshooting

### Registry Auth Issues
```bash
podman login 10.0.0.6:5000 -u admin -p <password> --tls-verify=false
```

### Build Fails with Cached Artifacts
Clean local TGE build artifacts:
```bash
rm -rf tge-152-fork/lib/out.GCC4.RELEASE tge-152-fork/engine/out.GCC4.RELEASE
```

### Container Won't Start
Check if pytge.so loaded correctly:
```bash
podman logs mom-server 2>&1 | head -50
```
