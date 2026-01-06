#!/bin/bash
# Setup Wine environment for Minions of Mirth Server
# This script creates a 32-bit Wine prefix for running the server

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WINE_PREFIX="${HOME}/.wine-mom"

echo "==================================="
echo "MoM Server - Wine Environment Setup"
echo "==================================="
echo ""

# Check if Wine is installed
if ! command -v wine &> /dev/null; then
    echo "ERROR: Wine is not installed!"
    echo ""
    echo "Please install Wine first:"
    echo "  sudo dpkg --add-architecture i386"
    echo "  sudo apt update"
    echo "  sudo apt install wine64 wine32 winetricks"
    exit 1
fi

echo "Wine version: $(wine --version)"
echo ""

# Set up Wine prefix
export WINEPREFIX="$WINE_PREFIX"
export WINEARCH=win32

if [ -d "$WINE_PREFIX" ]; then
    echo "Wine prefix already exists at: $WINE_PREFIX"
    read -p "Do you want to recreate it? This will delete existing data! (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing Wine prefix..."
        rm -rf "$WINE_PREFIX"
    else
        echo "Using existing Wine prefix."
    fi
fi

if [ ! -d "$WINE_PREFIX" ]; then
    echo "Creating new 32-bit Wine prefix at: $WINE_PREFIX"
    wineboot -i
    echo "Waiting for Wine to initialize..."
    sleep 3
    wineserver -w
fi

echo ""
echo "==================================="
echo "Wine Environment Setup Complete!"
echo "==================================="
echo ""
echo "Wine Prefix: $WINE_PREFIX"
echo ""
echo "Next steps:"
echo "  1. Run ./install-python-wine.sh to install Python 2.7"
echo "  2. Run ./install-dependencies-wine.sh to install required packages"
echo "  3. Run ./run-mom-server.sh to start the servers"
echo ""
