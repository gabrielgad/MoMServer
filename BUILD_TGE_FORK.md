# Building TGE Fork for MoM Server (Linux)

This document explains how to build the Torque Game Engine (TGE) Python bindings (`pytge.so` and `tgenative.so`) from source for Linux. This is **required** to run MoM Server zones on Linux, as the Windows binaries (`.pyd` files) won't work.

## Overview

The MoM Server requires two critical Python extension modules:
- **pytge.so**: Core TGE engine bindings (game loop, rendering, physics, mission loading)
- **tgenative.so**: TGE global variable access (TGEGetGlobal, TGESetGlobal, TGEEval)

These modules bridge Python code with the C++ Torque Game Engine.

---

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu/Debian recommended, tested on similar distros)
- **Architecture**: x86_64 (64-bit) or i686 (32-bit, depending on your Python)
- **RAM**: 4GB minimum
- **Disk Space**: ~2GB for source + build artifacts

### Required Tools

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    git \
    nasm \
    libx11-dev \
    libxext-dev \
    libxxf86vm-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libopenal-dev \
    libvorbis-dev \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    zlib1g-dev \
    python2.7-dev \
    swig

# CentOS/RHEL/Fedora
sudo yum groupinstall "Development Tools"
sudo yum install -y \
    cmake \
    git \
    nasm \
    libX11-devel \
    libXext-devel \
    libXxf86vm-devel \
    mesa-libGL-devel \
    mesa-libGLU-devel \
    openal-soft-devel \
    libvorbis-devel \
    freetype-devel \
    libpng-devel \
    libjpeg-turbo-devel \
    zlib-devel \
    python27-devel \
    swig
```

### Python Requirements
```bash
# Verify Python 2.7 is installed
python2.7 --version

# Install pip for Python 2.7 (if not present)
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py
python2.7 get-pip.py

# Install Python development headers (if not installed above)
# Ubuntu/Debian
sudo apt-get install python2.7-dev

# CentOS/RHEL
sudo yum install python27-devel
```

---

## Step 1: Obtain TGE Fork Source Code

### Option A: tge-fork-152 (If you have the specific repository)

```bash
cd ~
git clone https://github.com/YOUR_ORG/tge-fork-152.git
cd tge-fork-152
git checkout 152  # or the specific commit/tag
```

**Note**: Replace `YOUR_ORG/tge-fork-152` with the actual repository URL. The "152" likely refers to a specific commit, tag, or branch.

### Option B: TMMOKit/TGE Source (Alternative)

If you don't have access to tge-fork-152, you can try building from the original TGE source used by TMMOKit:

```bash
cd ~
# Prairie Games TGE (if available)
git clone https://github.com/PrairieGames/TorqueGameEngine.git tge-source
cd tge-source

# OR try the community TGE fork
git clone https://github.com/TorqueGameEngines/Torque2D.git tge-source
cd tge-source
```

### Option C: Extract from Minions of Mirth (Last Resort)

If you have a Windows MoM installation with source code:

```bash
# Copy the TGE source from Windows installation
# Look for: MinionsOfMirthUW/engine/source/ or similar
scp -r user@windows-machine:/path/to/MoM/engine/source ~/tge-source
```

---

## Step 2: Locate Python Binding Source

The TGE Python bindings are typically in:
```
tge-source/
├── engine/
│   └── python/          # Python binding source
│       ├── pytge.cpp    # Main TGE wrapper
│       ├── tgenative.cpp # Native functions wrapper
│       └── setup.py     # Python build script
├── lib/
│   └── python/          # Alternative location
└── tools/
    └── pytge/           # Another possible location
```

**Find the Python bindings:**
```bash
cd ~/tge-source
find . -name "pytge.cpp" -o -name "setup.py" | grep -i python
```

If not found, you may need to:
1. Check TMMOKit documentation for the correct TGE version
2. Contact the original MoM server developers
3. Reverse-engineer the bindings from the Windows `.pyd` file (very difficult)

---

## Step 3: Build the TGE Engine Library

Before building Python bindings, you must compile the core TGE engine.

### Configure Build

```bash
cd ~/tge-source

# Create build directory
mkdir -p build
cd build

# Configure with CMake (if available)
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DPYTHON_EXECUTABLE=/usr/bin/python2.7 \
    -DPYTHON_INCLUDE_DIR=/usr/include/python2.7 \
    -DBUILD_PYTHON_BINDINGS=ON \
    -DOPENAL_ENABLED=ON \
    -DOGG_VORBIS_ENABLED=ON

# OR use traditional configure (if no CMake)
cd ~/tge-source
./configure \
    --enable-python \
    --with-python=/usr/bin/python2.7 \
    --enable-openal \
    --enable-vorbis \
    --prefix=/usr/local
```

### Compile TGE

```bash
# If using CMake
cd ~/tge-source/build
make -j$(nproc)

# If using Makefile
cd ~/tge-source
make -j$(nproc)
```

**Expected build time**: 10-60 minutes depending on CPU

**Common build errors**:
- **Missing headers**: Install missing -dev/-devel packages
- **Python.h not found**: `sudo apt-get install python2.7-dev`
- **OpenAL errors**: `sudo apt-get install libopenal-dev`
- **X11 errors**: `sudo apt-get install libx11-dev libxext-dev`

---

## Step 4: Build Python Bindings (pytge.so)

### Method 1: Using setup.py (Recommended)

```bash
cd ~/tge-source/engine/python  # Or wherever pytge source is located

# Build the extension
python2.7 setup.py build

# This should create:
# build/lib.linux-x86_64-2.7/pytge.so
# build/lib.linux-x86_64-2.7/tgenative.so

# Install to Python site-packages (optional)
python2.7 setup.py install

# OR copy manually to MOM_INSTALL
cp build/lib.*/pytge.so $MOM_INSTALL/
cp build/lib.*/tgenative.so $MOM_INSTALL/
```

### Method 2: Manual Compilation with gcc

If no setup.py exists, compile manually:

```bash
cd ~/tge-source/engine/python

# Compile pytge.cpp to pytge.so
gcc -shared -fPIC \
    -I/usr/include/python2.7 \
    -I../../engine \
    -I../../lib \
    -L../../build \
    -ltorque \
    -lGL -lGLU -lX11 -lopenal -lvorbisfile \
    pytge.cpp -o pytge.so \
    -std=c++11

# Compile tgenative.cpp to tgenative.so
gcc -shared -fPIC \
    -I/usr/include/python2.7 \
    -I../../engine \
    tgenative.cpp -o tgenative.so \
    -std=c++11

# Copy to MOM_INSTALL
cp pytge.so $MOM_INSTALL/
cp tgenative.so $MOM_INSTALL/
```

### Method 3: Using SWIG (If bindings use SWIG)

```bash
cd ~/tge-source/engine/python

# Generate Python wrapper from SWIG interface
swig -python -c++ pytge.i

# Compile the SWIG-generated code
python2.7 setup.py build_ext --inplace

# Copy to MOM_INSTALL
cp pytge.so $MOM_INSTALL/
cp tgenative.so $MOM_INSTALL/
```

---

## Step 5: Verify the Binaries

```bash
# Check the built binaries exist
ls -lh pytge.so tgenative.so

# Check dependencies
ldd pytge.so
# Should show: libGL.so, libX11.so, libopenal.so, etc.

# Test import in Python
python2.7 -c "import pytge; print('pytge loaded successfully')"
python2.7 -c "from tgenative import TGEGetGlobal; print('tgenative loaded successfully')"
```

**Expected output:**
```
pytge loaded successfully
tgenative loaded successfully
```

**Common errors:**
- **ImportError: undefined symbol**: Missing library dependency
  - Solution: `ldd pytge.so` to identify missing libs, install them
- **ImportError: libTorque.so not found**: TGE engine library not in LD_LIBRARY_PATH
  - Solution: `export LD_LIBRARY_PATH=/path/to/tge-build:$LD_LIBRARY_PATH`
- **Segmentation fault**: ABI mismatch (Python version, 32/64-bit)
  - Solution: Rebuild with correct Python version flags

---

## Step 6: Configure MoM Server to Use Built Binaries

### Set Environment Variables

```bash
# Create a launch script
cat > ~/MoMServer/run_server.sh << 'EOF'
#!/bin/bash

# Set MOM_INSTALL to where you copied the .so files
export MOM_INSTALL=/opt/MinionsOfMirth

# Add TGE libraries to library path
export LD_LIBRARY_PATH=$MOM_INSTALL:$MOM_INSTALL/lib:$LD_LIBRARY_PATH

# Set Python path
export PYTHONPATH=$MOM_INSTALL:$MOM_INSTALL/library.zip:$PYTHONPATH

# Navigate to server directory
cd ~/MoMServer

# Run the diagnostic
python2.7 check_installation.py

EOF

chmod +x ~/MoMServer/run_server.sh
```

### Directory Structure

Your `$MOM_INSTALL` should now contain:
```
/opt/MinionsOfMirth/
├── pytge.so              # Built from source ✓
├── tgenative.so          # Built from source ✓
├── common/               # Copied from Windows MoM
├── minions.of.mirth/     # Copied from Windows MoM
├── library.zip           # Python modules from MoM (optional)
├── mud/                  # Core game logic (from library.zip or extracted)
├── main.cs.dso           # Compiled TorqueScript
└── lib/                  # TGE shared libraries
    └── libTorque.so      # TGE engine library
```

---

## Step 7: Test the Integration

```bash
cd ~/MoMServer

# Run diagnostic
python2.7 check_installation.py

# If all checks pass, try starting a zone server test
python2.7 -c "
import sys
sys.argv = ['test', '-game', 'minions.of.mirth']
import pytorque
print('Calling pytorque.Init()...')
pytorque.Init(sys.argv)
print('SUCCESS: pytorque.Init() completed!')
pytorque.Shutdown()
"
```

**Expected success output:**
```
Calling pytorque.Init()...
Initialising Torque Game Engine...
Loading mission files...
SUCCESS: pytorque.Init() completed!
```

**If it hangs**: Mission files are missing or corrupted (see MINIMAL_INSTALL.md)

---

## Troubleshooting

### Build Fails with Missing Headers

```bash
# Find missing header
grep -r "HEADER_NAME.h" /usr/include/

# Install package providing the header
apt-file search HEADER_NAME.h  # Debian/Ubuntu
yum provides */HEADER_NAME.h   # CentOS/RHEL
```

### Python Import Fails with Symbol Errors

```bash
# Check which symbols are undefined
nm -D pytge.so | grep "U "

# Check which symbols the TGE lib provides
nm -D libTorque.so | grep "T "

# Ensure TGE lib is in library path
export LD_LIBRARY_PATH=/path/to/tge-build:$LD_LIBRARY_PATH
```

### Binary is Wrong Architecture

```bash
# Check binary architecture
file pytge.so
# Should match: ELF 64-bit LSB shared object, x86-64

# Check Python architecture
python2.7 -c "import platform; print(platform.architecture())"
# Should match: ('64bit', 'ELF')

# If mismatch, rebuild with correct flags:
# For 32-bit: CFLAGS="-m32" python2.7 setup.py build
# For 64-bit: CFLAGS="-m64" python2.7 setup.py build
```

### Segfault on Import

Usually ABI incompatibility:
```bash
# Verify Python version used to build
python2.7-config --cflags
python2.7-config --ldflags

# Rebuild with explicit flags
CFLAGS="$(python2.7-config --cflags)" \
LDFLAGS="$(python2.7-config --ldflags)" \
python2.7 setup.py build
```

---

## Alternative: Cross-Compile from Windows

If building on Linux is too difficult, you can cross-compile:

```bash
# Install MinGW cross-compiler on Linux
sudo apt-get install mingw-w64

# Build Windows binaries on Linux
i686-w64-mingw32-gcc -shared -o pytge.pyd pytge.cpp \
    -I/path/to/python27-windows/include \
    -L/path/to/python27-windows/libs \
    -lpython27

# Use these .pyd files on Windows server
```

---

## tge-fork-152 Specific Notes

If you're specifically evaluating **tge-fork-152**:

1. **Identify what "152" means**:
   ```bash
   cd tge-fork-152
   git log --oneline | grep -i "152"
   git tag | grep "152"
   ```

2. **Check for fork-specific changes**:
   ```bash
   # Compare with upstream TGE
   git log --oneline --graph --decorate --all
   ```

3. **Look for build documentation**:
   ```bash
   cat README.md BUILD.md INSTALL.txt
   ls -la docs/
   ```

4. **Check for pre-built binaries**:
   ```bash
   find . -name "*.so" -o -name "*.pyd"
   # If found, you may not need to build!
   ```

---

## Next Steps

After successfully building the binaries:

1. ✅ Run `python2.7 check_installation.py` to verify
2. ✅ Read `MINIMAL_INSTALL.md` for complete setup
3. ✅ Set up game content (common/, minions.of.mirth/)
4. ✅ Run `Install.py` to create databases
5. ✅ Start MasterServer, CharacterServer, WorldManager
6. ✅ Test zone startup

---

## Resources

- **TGE Documentation**: https://docs.torque3d.org/
- **TMMOKit Forums**: https://realmcrafter.boards.net/thread/99/
- **Archived TMMOKit Docs**: https://web.archive.org/web/20111210231923/http://www.mmoworkshop.com/trac/mom/wiki/
- **Python C Extension Guide**: https://docs.python.org/2.7/extending/extending.html
- **SWIG Documentation**: http://www.swig.org/Doc2.0/Python.html

---

## Support

If you encounter issues building tge-fork-152:

1. Check `check_installation.py` output for specific errors
2. Review TGE build logs for compilation errors
3. Verify Python version compatibility (must be 2.7)
4. Ensure all dependencies are installed
5. Consider using the original TMMOKit TGE version instead

**Note**: Building TGE from source is complex. If you have access to a working Windows MoM installation, it's much easier to copy the pre-built `pytge.pyd` and `tgenative.pyd` files and run the server on Windows.
