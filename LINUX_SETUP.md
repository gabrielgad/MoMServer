# Minions of Mirth Server - Linux Setup Guide

This document outlines two approaches for running the MoM server on Linux:
1. **Wine Approach** (Primary) - Run Windows dependencies through Wine
2. **Build from Source** (Fallback) - Build Torque Game Engine natively for Linux

## Option 1: Wine Approach (Recommended to try first)

### Overview
Run the Windows version of Python 2.7 and all dependencies through Wine, avoiding the need to build Torque from source.

### Prerequisites
- Wine installed (preferably Wine 8.0+)
- winetricks for managing Wine components
- Minions of Mirth game files (can be obtained from a Windows install or extracted)

### Installation Steps

#### 1. Install Wine and Dependencies
```bash
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install wine64 wine32 winetricks
```

#### 2. Set up Wine Prefix (32-bit)
The MoM server requires 32-bit Python and libraries:
```bash
export WINEPREFIX="$HOME/.wine-mom"
export WINEARCH=win32
wineboot
```

#### 3. Install Python 2.7 in Wine
```bash
# Download Python 2.7.18 (last 2.7 release)
wget https://www.python.org/ftp/python/2.7.18/python-2.7.18.msi

# Install via Wine
wine msiexec /i python-2.7.18.msi /qn TARGETDIR=C:\\Python27

# Verify installation
wine "C:\\Python27\\python.exe" --version
```

#### 4. Install wxPython 2.8.x
```bash
# Download wxPython 2.8.12.1 (unicode version for Python 2.7)
wget https://downloads.sourceforge.net/wxpython/wxPython2.8-win32-unicode-2.8.12.1-py27.exe

# Install via Wine
wine wxPython2.8-win32-unicode-2.8.12.1-py27.exe /S
```

#### 5. Install OpenSSL (32-bit)
```bash
# Use winetricks or download from slproweb.com
winetricks vcrun2010  # Often needed for OpenSSL

# Alternative: Manual download
# wget https://slproweb.com/download/Win32OpenSSL-1_1_1w.exe
# wine Win32OpenSSL-1_1_1w.exe /SILENT
```

#### 6. Install Python Dependencies
```bash
wine "C:\\Python27\\python.exe" -m pip install --upgrade pip
wine "C:\\Python27\\python.exe" -m pip install -r requirements.txt
```

#### 7. Set Up MoM Game Files
You'll need the Minions of Mirth game installation. Options:
- Copy from Windows install
- Extract from installer
- Mount/extract game archive

Place in: `$WINEPREFIX/drive_c/Program Files/MinionsOfMirthUW/`

#### 8. Configure Environment
Create a wrapper script `run-mom-server.sh`:
```bash
#!/bin/bash
export WINEPREFIX="$HOME/.wine-mom"
export MOM_INSTALL="C:\\Program Files\\MinionsOfMirthUW"
export PYTHONPATH="C:\\Python27\\Lib\\site-packages;$MOM_INSTALL;$MOM_INSTALL\\library.zip;"

PYTHON="wine C:\\Python27\\python.exe"

case "$1" in
    install)
        $PYTHON Install.py
        ;;
    master)
        $PYTHON MasterServer.py gameconfig=mom.cfg
        ;;
    gm)
        $PYTHON GMServer.py gameconfig=mom.cfg
        ;;
    character)
        $PYTHON CharacterServer.py gameconfig=mom.cfg
        ;;
    world-manager)
        $PYTHON WorldManager.py gameconfig=mom.cfg
        ;;
    *)
        echo "Usage: $0 {install|master|gm|character|world-manager}"
        exit 1
        ;;
esac
```

#### 9. Run Installation Script
```bash
chmod +x run-mom-server.sh
./run-mom-server.sh install
```

#### 10. Start Servers
In separate terminals:
```bash
./run-mom-server.sh master
./run-mom-server.sh gm
./run-mom-server.sh character
./run-mom-server.sh world-manager
```

### Known Issues with Wine Approach
- wxPython GUI may have rendering issues
- Some Wine versions have compatibility problems with older Python packages
- Network binding might need special Wine configuration
- Performance overhead from Wine layer

### Troubleshooting Wine Setup
```bash
# Check Wine version
wine --version

# Verify Python installation
wine "C:\\Python27\\python.exe" --version

# List installed packages
wine "C:\\Python27\\python.exe" -m pip list

# Check for missing DLLs
wine "C:\\Python27\\python.exe" -c "import wx; print(wx.VERSION_STRING)"
```

---

## Option 2: Build from Source (Fallback)

### Overview
Build the Torque Game Engine from source for native Linux execution. This is more complex but provides better performance and avoids Wine compatibility issues.

### Prerequisites
- Build tools: gcc, g++, make, cmake
- Development libraries for the Torque Game Engine
- Python 2.7 (native Linux)
- wxPython 2.8.x (native Linux - challenging to find)

### Installation Steps

#### 1. Install System Dependencies
```bash
sudo apt update
sudo apt install build-essential cmake git
sudo apt install libgl1-mesa-dev libglu1-mesa-dev
sudo apt install libopenal-dev libvorbis-dev
sudo apt install libsdl2-dev libfreetype6-dev
```

#### 2. Install Python 2.7 (Native)
```bash
# Python 2.7 is EOL, may need to build from source or use deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python2.7 python2.7-dev
```

#### 3. Install pip for Python 2.7
```bash
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py
python2.7 get-pip.py
```

#### 4. Install Python Dependencies
```bash
python2.7 -m pip install -r requirements.txt
```

#### 5. Install wxPython 2.8.x (Major Challenge)
This is extremely difficult on modern Linux:
```bash
# Option A: Try to find pre-built package (unlikely to work)
sudo apt install python-wxgtk2.8

# Option B: Build from source (complex, time-consuming)
# Download wxPython 2.8.12.1 source
# Follow build instructions (out of scope here)

# Option C: Use wxPython 4.x and update code (requires code changes)
python2.7 -m pip install wxPython
```

#### 6. Build Torque Game Engine
```bash
# Clone Torque source (need to find appropriate version)
# TMMOKit was based on Torque Game Engine - need to identify exact version

git clone https://github.com/GarageGames/Torque3D.git
cd Torque3D

# Checkout appropriate version for MoM compatibility
# (Version identification required - likely very old version)

# Build
mkdir build && cd build
cmake ..
make -j$(nproc)
```

#### 7. Integrate Torque with MoM Server
This requires:
- Understanding how `pytorque.py` interfaces with Torque
- Rebuilding or finding Python bindings for Torque
- Potentially recompiling with Python support

**This step is complex and may require significant reverse engineering**

### Challenges with Build from Source
- Torque Game Engine version compatibility unknown
- Python bindings for Torque may not exist for Linux
- wxPython 2.8.x is EOL and incompatible with modern Linux
- May require extensive code modifications
- Time investment: days to weeks

---

## Recommendation

**Start with the Wine approach** because:
1. Faster to set up (hours vs days)
2. Uses exact versions the code was designed for
3. No code modifications needed
4. Can fall back to build-from-source if Wine issues are insurmountable

**Consider build-from-source only if:**
- Wine performance is unacceptable
- Wine compatibility issues can't be resolved
- You need native Linux integration
- You're willing to invest significant time in porting

---

## Next Steps

1. Try Wine approach first
2. Document any issues encountered
3. If Wine fails, assess build-from-source feasibility
4. Consider modernization (Python 3, newer libraries) as long-term goal

## Resources
- TMMOKit Documentation: https://web.archive.org/web/20111210231923/http://www.mmoworkshop.com/trac/mom/wiki/Documentation
- Wine HQ: https://www.winehq.org/
- Python 2.7 (archived): https://www.python.org/downloads/release/python-2718/
- wxPython 2.8 (archived): https://sourceforge.net/projects/wxpython/files/wxPython/2.8.12.1/
