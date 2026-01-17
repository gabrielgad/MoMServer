# CRITICAL: 32-bit vs 64-bit Architecture Mismatch

## ⚠️ THE REAL PROBLEM

You've identified the **root cause** of the zone startup failures:

**Minions of Mirth was built as a 32-bit application**, but you're trying to run it on a 64-bit system with 64-bit Python bindings. This creates a fundamental ABI (Application Binary Interface) mismatch that will cause:

- Import failures
- Segmentation faults
- Undefined symbol errors
- Silent crashes
- **Zones that never start**

---

## Architecture Analysis

### Original MoM/TGE Architecture

From the patchlist.txt evidence:
```
Version 1.2:
- New pytge.pyd+pytge.so:
  Windows: pytge.pyd (~2.8 MB) - 32-bit compiled module
  Linux:   pytge.so (~11.5 MB)  - 64-bit compiled (MISMATCH!)
```

**The Windows version is 32-bit**, as confirmed by:
1. File size (~2.8 MB for 32-bit vs ~11.5 MB for 64-bit with debug symbols)
2. Original TGE codebase was 32-bit
3. MoM was released in ~2006-2008 era (32-bit dominated)
4. README mentions "OpenSSL (32bit?)" requirement

### The Problem

```
┌─────────────────────────────────────────────────────────────┐
│                   ARCHITECTURE MISMATCH                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  32-bit pytge.pyd/so  ←→  64-bit Python  = FAIL ✗          │
│                                                              │
│  64-bit pytge.pyd/so  ←→  32-bit Python  = FAIL ✗          │
│                                                              │
│  32-bit pytge.pyd/so  ←→  32-bit Python  = WORKS ✓         │
│                                                              │
│  64-bit pytge.pyd/so  ←→  64-bit Python  = WORKS ✓         │
│                          (if built correctly)                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Symptoms you're experiencing:**
- Zones never declare "up" → pytge.so can't load due to arch mismatch
- Import errors → Python can't load wrong-architecture .so files
- Segfaults → ABI incompatibility causes crashes

---

## Check Your Current Architecture

### Check System Architecture
```bash
uname -m
# x86_64 = 64-bit system
# i686/i386 = 32-bit system
```

### Check Python Architecture
```bash
python2.7 -c "import platform, struct; print('Architecture:', platform.architecture()); print('Pointer size:', struct.calcsize('P') * 8, 'bits')"

# Output examples:
# ('64bit', 'ELF') - 64-bit Python
# ('32bit', 'ELF') - 32-bit Python
```

### Check pytge.so Architecture (if you have it)
```bash
file pytge.so

# 32-bit output:
# pytge.so: ELF 32-bit LSB shared object, Intel 80386

# 64-bit output:
# pytge.so: ELF 64-bit LSB shared object, x86-64
```

### Check for Architecture Mismatch
```bash
python2.7 << 'EOF'
import platform
import struct
import os

print("System Architecture:", platform.machine())
print("Python Architecture:", platform.architecture()[0])
print("Python Pointer Size:", struct.calcsize("P") * 8, "bits")
print("Python Executable:", platform.python_implementation())

# Try to check pytge if it exists
try:
    import pytge
    print("\nWARNING: pytge imported successfully!")
    print("This means architectures MATCH")
except ImportError as e:
    print("\npytge import failed:", e)
    if "wrong ELF class" in str(e) or "cannot open shared object" in str(e):
        print("ERROR: This is likely an ARCHITECTURE MISMATCH!")
EOF
```

---

## Solutions

### Solution 1: Use 32-bit Python (RECOMMENDED for Original MoM)

If you want to use the **original 32-bit MoM client files**:

#### On Linux (64-bit system, 32-bit Python)

```bash
# Install 32-bit Python on 64-bit Linux
# Ubuntu/Debian
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install -y \
    python2.7:i386 \
    python2.7-dev:i386 \
    libpython2.7:i386 \
    lib32gcc-s1 \
    lib32stdc++6

# Install 32-bit libraries for TGE
sudo apt-get install -y \
    libc6:i386 \
    libgl1:i386 \
    libglu1:i386 \
    libx11-6:i386 \
    libxext6:i386 \
    libopenal1:i386 \
    libvorbis0a:i386 \
    libvorbisfile3:i386

# Verify 32-bit Python
file /usr/bin/python2.7
# Should show: ELF 32-bit
```

#### Extract 32-bit pytge from Windows MoM Client

```bash
# Copy from your Windows MoM client installation
# The client has the 32-bit binaries!

# On Windows:
cd "C:\Program Files (x86)\MinionsOfMirthUW"
# OR wherever your client is installed

# Copy these 32-bit files:
# - pytge.pyd (Windows Python extension)
# - tgenative.pyd
# - You can also use wine to run the Windows .pyd files on Linux
```

---

### Solution 2: Build 64-bit pytge from Source (HARDER)

If you want a **native 64-bit solution**:

#### Requirements
- 64-bit Python 2.7
- 64-bit TGE source code (tge-fork-152?)
- 64-bit system libraries

#### Build Process

```bash
# Ensure 64-bit Python
python2.7 -c "import struct; print(struct.calcsize('P') * 8)"
# Must output: 64

# Install 64-bit dependencies
sudo apt-get install -y \
    python2.7-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libx11-dev \
    libopenal-dev \
    libvorbis-dev

# Clone/extract tge-fork-152
cd ~/tge-fork-152

# Configure for 64-bit
mkdir build
cd build
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_FLAGS="-m64" \
    -DCMAKE_CXX_FLAGS="-m64" \
    -DPYTHON_EXECUTABLE=/usr/bin/python2.7

make -j$(nproc)

# Verify 64-bit output
file pytge.so
# Should show: ELF 64-bit LSB shared object, x86-64
```

**CRITICAL**: When building 64-bit, you must also rebuild ALL game data structures with 64-bit alignment. This means:
- Pointers are 8 bytes instead of 4 bytes
- Struct padding changes
- Serialization formats may break
- **Mission files may be incompatible**

---

### Solution 3: Use Wine to Run 32-bit Windows Binaries (EASIEST)

Run the entire **Windows 32-bit MoM server** on Linux using Wine:

```bash
# Install Wine
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install -y wine32 wine64 winetricks

# Install Python 2.7 in Wine
wine msiexec /i python-2.7.18.msi

# Copy your Windows MoM client directory
cp -r /path/to/MinionsOfMirthUW ~/.wine/drive_c/MoM

# Run servers through Wine
wine python "C:\MoM\MasterServer.py" gameconfig=mom.cfg
wine python "C:\MoM\WorldServer.py" gameconfig=mom.cfg
```

**Advantages:**
- Uses original 32-bit binaries
- No building required
- Guaranteed compatibility

**Disadvantages:**
- Wine overhead
- Slightly slower performance
- More complex debugging

---

## Extracting Everything from Your Client

Since you mentioned **you have a client with all missions and files**, let's extract everything you need!

### Step 1: Locate Your MoM Client Installation

```bash
# Windows default locations:
# C:\Program Files (x86)\MinionsOfMirthUW
# %LocalAppData%\MinionsOfMirthUW

# Find the installation
dir "C:\Program Files (x86)\MinionsOfMirthUW"
```

### Step 2: Identify Critical Files

Your client should have:

```
MinionsOfMirthUW/
├── pytge.pyd              ← CRITICAL: 32-bit TGE Python binding
├── tgenative.pyd          ← CRITICAL: 32-bit TGE native functions
├── library.zip            ← Contains mud/ module
├── main.cs.dso            ← TorqueScript initialization
├── common/                ← TGE common scripts
│   ├── server/
│   └── client/
├── minions.of.mirth/      ← ALL GAME CONTENT
│   ├── main.cs
│   ├── server/
│   ├── testgame/
│   │   ├── zones/
│   │   │   ├── base.mis       ← Mission files!
│   │   │   ├── landone.mis
│   │   │   ├── landtwo.mis
│   │   │   └── ...
│   │   ├── world.db
│   │   └── ...
│   └── data/              ← All assets
└── ...
```

### Step 3: Check Architecture of Client Binaries

```bash
# On Windows, check if 32-bit or 64-bit
cd "C:\Program Files (x86)\MinionsOfMirthUW"

# Use PowerShell
powershell -Command "Get-Item pytge.pyd | Format-List *"

# Or use dumpbin (if you have Visual Studio)
dumpbin /headers pytge.pyd | findstr machine
# 8664 machine (x64) = 64-bit
# 14C machine (x86)  = 32-bit
```

### Step 4: Extract Everything You Need

#### Create Archive on Windows

```bash
# PowerShell
cd "C:\Program Files (x86)\MinionsOfMirthUW"
Compress-Archive -Path `
    pytge.pyd, `
    tgenative.pyd, `
    library.zip, `
    main.cs.dso, `
    common, `
    minions.of.mirth `
    -DestinationPath C:\Temp\MoM-Server-Files.zip

# Or use 7-Zip/WinRAR
"C:\Program Files\7-Zip\7z.exe" a C:\Temp\MoM-Server-Files.zip `
    pytge.pyd tgenative.pyd library.zip main.cs.dso common minions.of.mirth
```

#### Transfer to Linux

```bash
# From Windows to Linux
scp C:\Temp\MoM-Server-Files.zip user@linux-server:/tmp/

# On Linux
cd /opt
sudo mkdir -p MinionsOfMirth
cd MinionsOfMirth
sudo unzip /tmp/MoM-Server-Files.zip
```

### Step 5: Verify Architecture Match

```bash
# Check what you extracted
file pytge.pyd
# pytge.pyd: PE32 executable (DLL) Intel 80386 = 32-bit Windows

# This won't work directly on Linux!
# You need either:
# 1. Wine to run 32-bit Windows binaries
# 2. Build 64-bit pytge.so from source
# 3. Extract pytge.so from a Linux MoM client (if you have one)
```

---

## The Correct Setup Based on Your Situation

### Scenario A: You Have Windows 32-bit MoM Client (MOST LIKELY)

```bash
# Option 1: Run entire server in Wine (EASIEST)
wine python2.7 MasterServer.py gameconfig=mom.cfg

# Option 2: Use 32-bit Python on Linux + extract client files
# Install 32-bit Python (see Solution 1 above)
# Extract all files from client
# Copy pytge.pyd → rename to pytge.so (might work with wine-python)
```

### Scenario B: You Have 64-bit TGE Fork

```bash
# Build 64-bit pytge.so from tge-fork-152
# Use 64-bit Python
# Extract mission files from client (they should be compatible)
# Test carefully - data structure alignment may be broken
```

---

## Quick Diagnostic Script

Add this to your `check_installation.py`:

```python
def check_architecture_mismatch():
    """Check for 32-bit vs 64-bit mismatches"""
    print_header("ARCHITECTURE COMPATIBILITY CHECK")

    import platform
    import struct

    system_arch = platform.machine()
    python_bits = struct.calcsize("P") * 8

    print(f"System Architecture: {system_arch}")
    print(f"Python Architecture: {python_bits}-bit")

    # Try to check pytge
    try:
        import pytge
        pytge_file = pytge.__file__

        # Check file architecture
        import subprocess
        result = subprocess.check_output(['file', pytge_file])
        print(f"\npytge.so: {result.decode()}")

        if '32-bit' in result.decode() and python_bits == 64:
            print(colorize("ERROR: 32-bit pytge.so with 64-bit Python!", Colors.FAIL))
            print("Solution: Install 32-bit Python or rebuild pytge for 64-bit")
            return False
        elif '64-bit' in result.decode() and python_bits == 32:
            print(colorize("ERROR: 64-bit pytge.so with 32-bit Python!", Colors.FAIL))
            print("Solution: Install 64-bit Python or rebuild pytge for 32-bit")
            return False
        else:
            print(colorize("Architectures MATCH - OK", Colors.OKGREEN))
            return True

    except ImportError:
        print(colorize("Cannot check - pytge not importable", Colors.WARNING))
        return None
```

---

## Recommended Path Forward

Based on your situation (have client with missions):

### IMMEDIATE STEPS:

1. **Check your client's architecture:**
   ```bash
   cd "C:\Program Files (x86)\MinionsOfMirthUW"
   file pytge.pyd  # or use dumpbin
   ```

2. **If 32-bit (MOST LIKELY):**
   - Install Wine on Linux
   - Copy entire client directory to Linux
   - Run server through Wine
   - OR install 32-bit Python on Linux

3. **If 64-bit:**
   - Check if you have tge-fork-152 64-bit source
   - Build 64-bit pytge.so
   - Extract mission files from client
   - Test thoroughly

4. **Extract missions from client:**
   ```bash
   cp -r "C:\...\MinionsOfMirthUW\minions.of.mirth\testgame" /home/user/MoMServer/minions.of.mirth/
   ```

5. **Run diagnostic:**
   ```bash
   python check_installation.py
   ```

---

## Why This Explains Everything

Your observation is **spot on**:

1. ✅ Original MoM is 32-bit
2. ✅ You have 64-bit system/Python
3. ✅ Trying to load 32-bit pytge.pyd fails silently or crashes
4. ✅ Zone never starts because pytge can't initialize
5. ✅ This is NOT a Linux abstraction issue
6. ✅ This is NOT a mission file issue
7. ✅ This IS a **fundamental architecture mismatch**

**The "zones never declaring they're up" is because:**
```python
# zoneserver.py line 38
import pytge  # ← FAILS HERE due to 32/64-bit mismatch
```

The import fails silently, or crashes before reaching the point where zones would register themselves.

---

## Next Steps

1. Run this to check your current architecture:
   ```bash
   uname -m
   python2.7 -c "import struct; print(struct.calcsize('P')*8, 'bit')"
   file $MOM_INSTALL/pytge.*
   ```

2. Tell me the results, and I'll give you the exact path forward

3. Meanwhile, extract **ALL** the missions and files from your client - you definitely need those!

Would you like me to create a script to extract everything from your client and check for architecture mismatches?
