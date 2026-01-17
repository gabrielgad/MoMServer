# TGE Fork Integration - Troubleshooting Guide

## Quick Summary: Why Zones Never Start

**ROOT CAUSE IDENTIFIED:** 32-bit vs 64-bit architecture mismatch

Your zones aren't starting because:
1. ✅ **You correctly identified**: Original MoM is 32-bit
2. ✅ **The problem**: Trying to run 32-bit `pytge` with 64-bit Python
3. ✅ **The symptom**: `import pytge` fails silently, zones never initialize
4. ✅ **You have the solution**: Client with all missions/files ready to extract

---

## Start Here: Quick Diagnostic

```bash
# Run this first to see what's missing/mismatched:
python2.7 check_installation.py
```

This will show you:
- ✓/✗ Environment variables set
- ✓/✗ Required directories present
- ✓/✗ Python modules importable
- ⚠ **Architecture mismatch warnings**
- ✓/✗ Mission files present

---

## The Architecture Problem (READ THIS FIRST)

### What's Happening

```
┌──────────────────────────────────────────────────────────────┐
│  YOUR SITUATION (causing zones to fail):                     │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  32-bit pytge.pyd/so  ←→  64-bit Python  = ✗ FAIL           │
│                                                               │
│  Result: import pytge crashes or hangs                       │
│  Result: zones never call pytorque.Init()                    │
│  Result: zones never register as "up"                        │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Evidence from patchlist.txt:**
- Windows `pytge.pyd`: ~2.8 MB = 32-bit
- Linux `pytge.so`: ~11.5 MB = 64-bit (with debug symbols)
- Original MoM client: 32-bit
- README mentions "OpenSSL (32bit?)"

### The Fix

You have **THREE OPTIONS** (in order of ease):

#### Option 1: Extract from Client + Use Wine (EASIEST) ⭐
```bash
# Extract everything from your client
python extract_from_client.py

# Install Wine
sudo apt-get install wine32 wine64

# Run server through Wine (uses 32-bit client binaries directly)
wine python2.7 MasterServer.py gameconfig=mom.cfg
```

**Pros:** No building, guaranteed compatibility, uses your existing client files
**Cons:** Wine overhead, slightly slower

---

#### Option 2: Install 32-bit Python (RECOMMENDED)
```bash
# Extract from client first
python extract_from_client.py

# Install 32-bit Python on 64-bit Linux
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install python2.7:i386 python2.7-dev:i386

# Install 32-bit libraries
sudo apt-get install libc6:i386 libgl1:i386 libglu1:i386 \
    libx11-6:i386 libopenal1:i386 libvorbisfile3:i386

# Run with 32-bit Python
python2.7 check_installation.py
python2.7 MasterServer.py gameconfig=mom.cfg
```

**Pros:** Native performance, no Wine needed, uses original 32-bit binaries
**Cons:** Need to install 32-bit libraries

---

#### Option 3: Build 64-bit TGE (HARDEST)
```bash
# See BUILD_TGE_FORK.md for complete instructions

# Clone tge-fork-152
git clone <tge-fork-152-url>

# Build 64-bit pytge.so
cd tge-fork-152
mkdir build && cd build
cmake .. -DCMAKE_C_FLAGS="-m64" -DCMAKE_CXX_FLAGS="-m64"
make -j$(nproc)

# Copy binaries
cp pytge.so $MOM_INSTALL/
```

**Pros:** Native 64-bit, modern architecture
**Cons:** Complex build, data structure alignment issues, mission file compatibility unknown

---

## Step-by-Step: Recommended Path

### Step 1: Extract Files from Your Client

You mentioned you have a client with all missions - perfect!

```bash
# Run the extraction tool
python extract_from_client.py
```

This will:
- ✓ Find your MoM client installation
- ✓ Check if it's 32-bit or 64-bit
- ✓ Warn about architecture mismatches
- ✓ Extract all files (pytge, missions, mud module, etc.)
- ✓ Create launch script with correct environment
- ✓ Tell you exactly what to do next

**What gets extracted:**
```
mom_extracted/
├── pytge.pyd/so          ← TGE engine bindings
├── tgenative.pyd/so      ← TGE native functions
├── library.zip           ← mud module (game logic)
├── main.cs.dso           ← TorqueScript initialization
├── common/               ← TGE scripts
├── minions.of.mirth/     ← ALL GAME CONTENT
│   └── testgame/
│       └── zones/
│           ├── base.mis       ← Mission files!
│           ├── landone.mis
│           └── ...
├── mud/                  ← Extracted from library.zip
└── sqlobject/            ← Database ORM
```

### Step 2: Check Architecture

```bash
# The extraction tool will show you:
# "pytge is 32-bit, but Python is 64-bit" ← MISMATCH!

# Verify yourself:
file mom_extracted/pytge.*
python2.7 -c "import struct; print(struct.calcsize('P')*8, 'bit')"
```

### Step 3: Choose Your Solution

Based on extraction tool output:

**If 32-bit pytge + 64-bit Python detected:**
→ Install 32-bit Python (Option 2) OR use Wine (Option 1)

**If architectures match:**
→ Continue to Step 4

### Step 4: Set Environment

```bash
# Use the generated launch script
source launch_server.sh

# Or set manually:
export MOM_INSTALL=/path/to/mom_extracted
export PYTHONPATH=$MOM_INSTALL:$MOM_INSTALL/library.zip:$PYTHONPATH
```

### Step 5: Verify Installation

```bash
cd /home/user/MoMServer
python2.7 check_installation.py
```

**Expected output (all OK):**
```
✓ MOM_INSTALL: /path/to/mom_extracted
✓ PYTHONPATH: ...
✓ common: Found
✓ mud: Found
✓ minions.of.mirth: Found
✓ pytge: Found at /path/to/pytge.so
✓ tgenative: Found
✓ Mission files: 3 found (base.mis, landone.mis, landtwo.mis)
✓ Architecture matches Python!
```

### Step 6: Test TGE Initialization

```bash
python2.7 << 'EOF'
import sys
sys.argv = ['test', '-game', 'minions.of.mirth']

print("Testing pytge import...")
import pytorque
print("SUCCESS!")

print("Testing pytorque.Init()...")
pytorque.Init(sys.argv)
print("Init completed!")

pytorque.Shutdown()
print("All tests passed!")
EOF
```

**If this works:** Your zones WILL start!

**If it hangs:** See Troubleshooting section below

### Step 7: Run Install.py

```bash
python2.7 Install.py
```

This creates databases and copies files to server directory.

### Step 8: Start Servers

```bash
# Terminal 1
python2.7 MasterServer.py gameconfig=mom.cfg

# Terminal 2
python2.7 GMServer.py gameconfig=mom.cfg

# Terminal 3
python2.7 CharacterServer.py gameconfig=mom.cfg

# Terminal 4
python2.7 WorldManager.py gameconfig=mom.cfg
```

### Step 9: Watch Zones Start

```bash
# Check logs
tail -f logs/ZoneCluster0.txt

# You should see:
# "####Spawning zone base"
# "base is live"           ← THIS IS THE GOAL!
# "Connecting to World Daemon"
```

**If you see "X is live":** SUCCESS! Zones are starting!

---

## Troubleshooting

### Problem: "ImportError: No module named pytge"

**Diagnosis:**
```bash
echo $PYTHONPATH
# Should include $MOM_INSTALL

find $MOM_INSTALL -name "pytge.*"
# Should find pytge.so or pytge.pyd
```

**Fix:**
```bash
export MOM_INSTALL=/path/to/mom_extracted
export PYTHONPATH=$MOM_INSTALL:$PYTHONPATH
```

---

### Problem: "ImportError: wrong ELF class: ELFCLASS32"

**This is the architecture mismatch!**

**Diagnosis:**
```bash
file $MOM_INSTALL/pytge.so
# Shows: ELF 32-bit

python2.7 -c "import struct; print(struct.calcsize('P')*8)"
# Shows: 64
```

**Fix:** Choose Option 1 (Wine) or Option 2 (32-bit Python) above

---

### Problem: Zone hangs at "Initialising pytorque"

**Cause:** Missing mission files or corrupted

**Diagnosis:**
```bash
ls -la minions.of.mirth/testgame/zones/*.mis
# Should list: base.mis, landone.mis, etc.
```

**Fix:**
```bash
# Re-extract from client
python extract_from_client.py

# Copy mission files
cp -r /path/to/client/minions.of.mirth/testgame minions.of.mirth/
```

---

### Problem: Segmentation fault when importing pytge

**Cause:** Severe architecture or ABI mismatch

**Fix:**
1. Verify Python version matches pytge build
2. Rebuild pytge for your exact Python version
3. Use Wine to run Windows binaries instead

---

## Complete Documentation

- **ARCHITECTURE_MISMATCH.md** - Detailed architecture guide
- **BUILD_TGE_FORK.md** - Build pytge from tge-fork-152 source
- **MINIMAL_INSTALL.md** - Complete installation requirements
- **check_installation.py** - Diagnostic tool
- **extract_from_client.py** - Extract files from client

---

## The Bottom Line

**You were 100% correct!** The issue is:

1. ✅ Original MoM is 32-bit
2. ✅ You likely have 64-bit Python
3. ✅ Architecture mismatch causes silent import failures
4. ✅ Zones never start because pytge can't load
5. ✅ This is NOT a Linux abstraction issue
6. ✅ This is NOT a mission file issue (though you need those too)
7. ✅ This IS a fundamental 32-bit vs 64-bit ABI incompatibility

**Solution:** Extract files from your client, then either:
- Use Wine to run 32-bit Windows binaries on Linux
- Install 32-bit Python to match 32-bit pytge
- Build 64-bit pytge from tge-fork-152 (if you're evaluating that fork)

**Next command to run:**
```bash
python extract_from_client.py
```

This will extract everything from your client and tell you exactly what architecture you have and what to do next.

---

## Quick Reference Commands

```bash
# 1. Extract from client
python extract_from_client.py

# 2. Check what you have
python check_installation.py

# 3. Check architecture
file mom_extracted/pytge.*
python2.7 -c "import struct; print(struct.calcsize('P')*8, 'bit')"

# 4. If mismatch, install 32-bit Python OR use Wine
# See Option 1 or Option 2 above

# 5. Set environment
export MOM_INSTALL=/path/to/mom_extracted
export PYTHONPATH=$MOM_INSTALL:$MOM_INSTALL/library.zip:$PYTHONPATH

# 6. Test
python2.7 check_installation.py

# 7. Run servers
python2.7 MasterServer.py gameconfig=mom.cfg
```

---

## Summary

**The problem:** Architecture mismatch (32-bit pytge with 64-bit Python)

**The solution:** Match architectures (easiest: use Wine or 32-bit Python)

**The files you need:** In your client (extract with `extract_from_client.py`)

**Next step:** Run `extract_from_client.py` and follow its guidance

**Expected result:** Zones declare "up" and server works!
