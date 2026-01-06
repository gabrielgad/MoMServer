#!/bin/bash
# Install Python 2.7 in Wine for Minions of Mirth Server

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WINE_PREFIX="${HOME}/.wine-mom"
DOWNLOADS_DIR="${SCRIPT_DIR}/.downloads"

export WINEPREFIX="$WINE_PREFIX"
export WINEARCH=win32

echo "========================================="
echo "MoM Server - Python 2.7 Installation"
echo "========================================="
echo ""

# Check Wine prefix exists
if [ ! -d "$WINE_PREFIX" ]; then
    echo "ERROR: Wine prefix not found at $WINE_PREFIX"
    echo "Please run ./setup-wine-env.sh first"
    exit 1
fi

# Create downloads directory
mkdir -p "$DOWNLOADS_DIR"

# Python 2.7.18 installer
PYTHON_INSTALLER="python-2.7.18.msi"
PYTHON_URL="https://www.python.org/ftp/python/2.7.18/${PYTHON_INSTALLER}"
PYTHON_PATH="$DOWNLOADS_DIR/$PYTHON_INSTALLER"

# Download Python if not already present
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Downloading Python 2.7.18..."
    wget -O "$PYTHON_PATH" "$PYTHON_URL"
else
    echo "Python installer already downloaded: $PYTHON_PATH"
fi

# Check if Python is already installed
if wine "C:\\Python27\\python.exe" --version 2>/dev/null | grep -q "Python 2.7"; then
    echo ""
    echo "Python 2.7 is already installed in Wine!"
    wine "C:\\Python27\\python.exe" --version
    echo ""
    read -p "Do you want to reinstall? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping Python installation."
        exit 0
    fi
fi

echo ""
echo "Installing Python 2.7.18 to C:\\Python27..."
echo "This may take a few minutes..."
echo ""

# Install Python silently
wine msiexec /i "$PYTHON_PATH" /qn TARGETDIR=C:\\Python27 ALLUSERS=1

# Wait for installation to complete
echo "Waiting for installation to complete..."
sleep 5
wineserver -w

echo ""
echo "Verifying Python installation..."

if wine "C:\\Python27\\python.exe" --version 2>&1 | grep -q "Python 2.7"; then
    echo ""
    echo "========================================="
    echo "Python 2.7 installed successfully!"
    echo "========================================="
    wine "C:\\Python27\\python.exe" --version
    echo ""
    echo "Next step: Run ./install-dependencies-wine.sh"
    echo ""
else
    echo ""
    echo "ERROR: Python installation verification failed!"
    echo "Please check the Wine logs for errors."
    exit 1
fi
