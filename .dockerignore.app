# .dockerignore.app - Minimal context for fast app builds
# Used by: ./scripts/build-app.sh
# Reduces context from 1.6GB+ to ~15MB

# Large source directories (already in tge-builder image)
tge-152-fork/
tmmokit_source/

# Game content directories (mounted as volumes)
minions.of.mirth/
testgame.mmo/
starter.mmo/

# Python virtual environments
venv/
venv2/
.venv/

# Archives and large files
*.zip
*.tar.gz
*.tar
*.7z

# Logs and runtime data
*.log
logs/
data/

# Python cache
*.pyc
*.pyo
__pycache__/
*.egg-info/

# Git
.git/
.gitignore

# IDE and editor files
.idea/
.vscode/
*.swp
*.swo
*~

# Docker files not needed in context
Dockerfile.32bit
Dockerfile.base-deps
Dockerfile.tge-builder
docker-compose*.yml
.dockerignore

# Scripts
scripts/

# Build artifacts
*.o
*.so
*.a
build/
