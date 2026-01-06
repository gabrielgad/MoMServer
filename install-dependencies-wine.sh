#!/bin/bash
# Install dependencies for Minions of Mirth Server in Wine
# This includes wxPython, OpenSSL, and Python packages

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WINE_PREFIX="${HOME}/.wine-mom"
DOWNLOADS_DIR="${SCRIPT_DIR}/.downloads"

export WINEPREFIX="$WINE_PREFIX"
export WINEARCH=win32

echo "========================================="
echo "MoM Server - Dependencies Installation"
echo "========================================="
echo ""

# Check Wine prefix exists
if [ ! -d "$WINE_PREFIX" ]; then
    echo "ERROR: Wine prefix not found at $WINE_PREFIX"
    echo "Please run ./setup-wine-env.sh first"
    exit 1
fi

# Check Python is installed
if ! wine "C:\\Python27\\python.exe" --version 2>&1 | grep -q "Python 2.7"; then
    echo "ERROR: Python 2.7 not found in Wine"
    echo "Please run ./install-python-wine.sh first"
    exit 1
fi

# Create downloads directory
mkdir -p "$DOWNLOADS_DIR"

echo "Python version:"
wine "C:\\Python27\\python.exe" --version
echo ""

# ===================================
# 1. Install pip (if not already present)
# ===================================
echo "Step 1: Checking pip installation..."
if ! wine "C:\\Python27\\python.exe" -m pip --version 2>/dev/null; then
    echo "Installing pip..."

    GET_PIP="get-pip.py"
    GET_PIP_PATH="$DOWNLOADS_DIR/$GET_PIP"

    if [ ! -f "$GET_PIP_PATH" ]; then
        wget -O "$GET_PIP_PATH" "https://bootstrap.pypa.io/pip/2.7/get-pip.py"
    fi

    wine "C:\\Python27\\python.exe" "$GET_PIP_PATH"
    echo "pip installed successfully!"
else
    echo "pip is already installed."
    wine "C:\\Python27\\python.exe" -m pip --version
fi

echo ""

# ===================================
# 2. Install Visual C++ Runtime (needed for some packages)
# ===================================
echo "Step 2: Installing Visual C++ Runtime..."
if command -v winetricks &> /dev/null; then
    winetricks -q vcrun2010 || echo "Note: vcrun2010 may already be installed"
else
    echo "WARNING: winetricks not found. Some packages may fail to install."
    echo "Install winetricks and run: winetricks -q vcrun2010"
fi

echo ""

# ===================================
# 3. Install wxPython 2.8.12.1
# ===================================
echo "Step 3: Installing wxPython 2.8.12.1..."

WXPYTHON_INSTALLER="wxPython2.8-win32-unicode-2.8.12.1-py27.exe"
WXPYTHON_URL="https://downloads.sourceforge.net/wxpython/${WXPYTHON_INSTALLER}"
WXPYTHON_PATH="$DOWNLOADS_DIR/$WXPYTHON_INSTALLER"

# Check if wxPython is already installed
if wine "C:\\Python27\\python.exe" -c "import wx; print(wx.VERSION_STRING)" 2>/dev/null | grep -q "2.8"; then
    echo "wxPython 2.8 is already installed!"
    wine "C:\\Python27\\python.exe" -c "import wx; print('wxPython version:', wx.VERSION_STRING)"
else
    if [ ! -f "$WXPYTHON_PATH" ]; then
        echo "Downloading wxPython 2.8.12.1..."
        wget -O "$WXPYTHON_PATH" "$WXPYTHON_URL" || {
            echo "ERROR: Failed to download wxPython from SourceForge"
            echo "You may need to download it manually from:"
            echo "  https://sourceforge.net/projects/wxpython/files/wxPython/2.8.12.1/"
            echo "Save as: $WXPYTHON_PATH"
            exit 1
        }
    fi

    echo "Installing wxPython..."
    wine "$WXPYTHON_PATH" /SILENT || {
        echo "WARNING: wxPython installation may have failed."
        echo "Try running manually: wine $WXPYTHON_PATH"
    }

    # Wait for installation
    sleep 5
    wineserver -w

    # Verify wxPython installation
    if wine "C:\\Python27\\python.exe" -c "import wx; print(wx.VERSION_STRING)" 2>/dev/null; then
        echo "wxPython installed successfully!"
    else
        echo "WARNING: wxPython import test failed. GUI features may not work."
    fi
fi

echo ""

# ===================================
# 4. Install OpenSSL (32-bit)
# ===================================
echo "Step 4: Installing OpenSSL..."

# Note: OpenSSL installation via Wine can be tricky
# We'll try using winetricks first, then manual download as fallback

if command -v winetricks &> /dev/null; then
    echo "Installing OpenSSL dependencies via winetricks..."
    winetricks -q vcrun6 || echo "vcrun6 may already be installed"

    # Note: There's no direct winetricks verb for Win32OpenSSL
    # User may need to install manually if pip packages fail
    echo "If SSL errors occur, manually install Win32OpenSSL from:"
    echo "  https://slproweb.com/products/Win32OpenSSL.html"
else
    echo "WARNING: winetricks not available. OpenSSL may need manual installation."
fi

echo ""

# ===================================
# 5. Install Python requirements
# ===================================
echo "Step 5: Installing Python package requirements..."

if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "Installing packages from requirements.txt..."
    echo ""

    # Upgrade pip first
    wine "C:\\Python27\\python.exe" -m pip install --upgrade pip setuptools

    # Install requirements
    # Note: Some packages may fail on Wine, we'll continue on error
    wine "C:\\Python27\\python.exe" -m pip install -r "$SCRIPT_DIR/requirements.txt" || {
        echo ""
        echo "WARNING: Some packages failed to install."
        echo "This is common with Wine. Trying individual packages..."
        echo ""

        # Try installing packages one by one
        while IFS= read -r package || [ -n "$package" ]; do
            # Skip empty lines and comments
            [[ -z "$package" || "$package" =~ ^# ]] && continue

            echo "Installing $package..."
            wine "C:\\Python27\\python.exe" -m pip install "$package" || {
                echo "WARNING: Failed to install $package"
            }
        done < "$SCRIPT_DIR/requirements.txt"
    }

    echo ""
    echo "Installed packages:"
    wine "C:\\Python27\\python.exe" -m pip list
else
    echo "ERROR: requirements.txt not found at $SCRIPT_DIR/requirements.txt"
    exit 1
fi

echo ""
echo "========================================="
echo "Dependencies Installation Complete!"
echo "========================================="
echo ""
echo "Verification:"
echo ""

# Verify critical imports
echo "Testing critical imports..."
wine "C:\\Python27\\python.exe" -c "import email; print('  email: OK')" 2>/dev/null || echo "  email: FAILED"
wine "C:\\Python27\\python.exe" -c "import pyasn1; print('  pyasn1: OK')" 2>/dev/null || echo "  pyasn1: FAILED"
wine "C:\\Python27\\python.exe" -c "import Crypto; print('  pycrypto: OK')" 2>/dev/null || echo "  pycrypto: FAILED"
wine "C:\\Python27\\python.exe" -c "import twisted; print('  Twisted: OK')" 2>/dev/null || echo "  Twisted: FAILED"
wine "C:\\Python27\\python.exe" -c "import zope.interface; print('  zope.interface: OK')" 2>/dev/null || echo "  zope.interface: FAILED"
wine "C:\\Python27\\python.exe" -c "import wx; print('  wxPython: OK (version ' + wx.VERSION_STRING + ')')" 2>/dev/null || echo "  wxPython: FAILED"

echo ""
echo "Next steps:"
echo "  1. Place MoM game files in the Wine prefix (see LINUX_SETUP.md)"
echo "  2. Run ./run-mom-server.sh install to run Install.py"
echo "  3. Start the servers with ./run-mom-server.sh"
echo ""
