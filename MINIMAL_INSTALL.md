# Minimal Installation Guide for MoM Server

This guide explains the **minimum required setup** to get MoM Server zones running, particularly focusing on resolving the "zones never declaring they're up" issue.

---

## Table of Contents

1. [Quick Overview](#quick-overview)
2. [Understanding the Architecture](#understanding-the-architecture)
3. [Minimum Required Components](#minimum-required-components)
4. [Step-by-Step Installation](#step-by-step-installation)
5. [Verifying Installation](#verifying-installation)
6. [Troubleshooting Zone Startup](#troubleshooting-zone-startup)
7. [Platform-Specific Notes](#platform-specific-notes)

---

## Quick Overview

### What This Repository Contains (✓)
- ✅ Server orchestration code (`mud_ext/`)
- ✅ Configuration templates (`projects/mom.cfg`, `serverconfig/`)
- ✅ Entry points (`MasterServer.py`, `WorldServer.py`, etc.)
- ✅ Documentation and tools

### What You Must Provide (✗)
- ❌ TGE Engine bindings (`pytge.so`/`.pyd`, `tgenative.so`/`.pyd`)
- ❌ Core game logic (`mud/` Python module)
- ❌ Game content (`minions.of.mirth/` directory with missions, assets, scripts)
- ❌ TGE configuration (`common/` directory, `main.cs.dso`)
- ❌ Environment variables (`MOM_INSTALL`, `PYTHONPATH`)

**Why zones don't start:** You're missing items from the second list.

---

## Understanding the Architecture

### How Zones Start (The Complete Flow)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. WorldServer.py                                               │
│    - Reads serverconfig/<worldname>.py                          │
│    - Calls THEWORLD.startZoneProcess("base")                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Spawns: python zoneserver.py -game minions.of.mirth ...     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. zoneserver.py imports:                                       │
│    ├─ from mud.gamesettings import *        ← NEEDS mud/       │
│    ├─ from mud.world.core import ...        ← NEEDS mud/       │
│    ├─ from mud.simulation.simmind import ... ← NEEDS mud/      │
│    └─ import pytorque                        ← NEEDS pytge.so  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. pytorque.Init(sys.argv)                                      │
│    ├─ Initializes TGE engine                                   │
│    ├─ Loads main.cs.dso                      ← NEEDS file      │
│    ├─ Executes TorqueScript from common/    ← NEEDS dir       │
│    └─ Loads mission from minions.of.mirth/  ← NEEDS .mis files│
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Zone registers with mud.world.theworld.World                │
│    └─ Calls liveZoneCallback() → WorldServer                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. WorldServer marks zone as "UP"                               │
│    └─ ConnectToDaemon() → Allows player connections            │
└─────────────────────────────────────────────────────────────────┘
```

**Your current status:** Failing at step 3 (imports fail) or step 4 (pytorque.Init hangs).

---

## Minimum Required Components

### 1. Environment Variables

**File**: Set in your shell or launch script

```bash
# MOM_INSTALL: Points to your Minions of Mirth game installation
export MOM_INSTALL=/opt/MinionsOfMirth   # Linux
# OR
set MOM_INSTALL=C:\Program Files (x86)\MinionsOfMirthUW  # Windows

# PYTHONPATH: Tells Python where to find game modules
export PYTHONPATH=$MOM_INSTALL:$MOM_INSTALL/library.zip:$PYTHONPATH  # Linux
# OR
set PYTHONPATH=%MOM_INSTALL%;%MOM_INSTALL%\library.zip;%PYTHONPATH%  # Windows
```

**Why needed:**
- `import mud` fails without this
- `import pytorque` fails without this
- Python can't find game modules

---

### 2. TGE Python Bindings

**Files**:
- `pytge.so` (Linux) / `pytge.pyd` (Windows)
- `tgenative.so` (Linux) / `tgenative.pyd` (Windows)

**Location**: Must be in `$MOM_INSTALL` or another directory in `PYTHONPATH`

**Size**:
- Windows: ~2.8 MB (pytge.pyd), ~500 KB (tgenative.pyd)
- Linux: ~11.5 MB (pytge.so), ~1 MB (tgenative.so)

**Source**:
- **Windows**: Comes with MoM installation (already built)
- **Linux**: Must build from source (see `BUILD_TGE_FORK.md`)

**What they do**:
```python
import pytorque
pytorque.Init(args)         # Initialize TGE engine
pytorque.Tick()             # Run one game frame
pytorque.Shutdown()         # Cleanup TGE

from tgenative import TGEGetGlobal, TGESetGlobal
TGESetGlobal("$Server::DedicatedSleeping", False)  # Set TGE variable
value = TGEGetGlobal("$Server::Port")              # Read TGE variable
```

**Verification**:
```bash
python2.7 -c "import pytorque; print(pytorque.__file__)"
python2.7 -c "from tgenative import TGEGetGlobal; print('OK')"
```

---

### 3. Core Game Logic Module (`mud/`)

**Directory Structure**:
```
mud/
├── __init__.py
├── gamesettings.py          # GAMEROOT, server IPs, configuration
├── world/
│   ├── __init__.py
│   ├── theworld.py          # World class - manages zones
│   ├── zone.py              # Zone class - individual zones
│   ├── core.py              # CoreSettings, utility functions
│   ├── spawn.py             # Mob/spawn management
│   ├── spell.py             # Spell system
│   ├── career.py            # Class/career system
│   ├── dialog.py            # NPC dialogs
│   ├── item.py              # Item system
│   ├── crafting.py          # Crafting/recipes
│   ├── loot.py              # Loot tables
│   ├── faction.py           # Faction system
│   ├── advancement.py       # Leveling/advancement
│   └── defines.py           # Constants
├── simulation/
│   ├── __init__.py
│   ├── simmind.py           # Zone simulation, NumPlayersInZone()
│   └── ...
├── common/
│   ├── __init__.py
│   └── dbconfig.py          # Database configuration
└── utils.py                 # Utility functions
```

**Location**:
- Option A: `$MOM_INSTALL/mud/` (extracted from library.zip)
- Option B: `$MOM_INSTALL/library.zip` (as a zip import)
- Option C: Copy to `/home/user/MoMServer/mud/` (local to server)

**Source**:
- Comes with MoM installation (in `library.zip`)
- OR from TMMOKit distribution

**Why needed**:
```python
# zoneserver.py line 167
from mud.gamesettings import *        # GAMEROOT, server config

# zoneserver.py line 168
from mud.world.core import CoreSettings  # Core game settings

# zoneserver.py line 188
from mud.simulation.simmind import NumPlayersInZone  # Zone player count
```

**Extraction** (if in library.zip):
```bash
cd $MOM_INSTALL
unzip library.zip -d .
# Now mud/ directory should exist
```

**Verification**:
```bash
python2.7 -c "import mud.gamesettings; print(mud.gamesettings.GAMEROOT)"
# Should print: minions.of.mirth
```

---

### 4. Game Content Directory (`minions.of.mirth/`)

**Directory Structure** (minimal):
```
minions.of.mirth/
├── main.cs                  # Main TorqueScript initialization
├── server/
│   └── scripts/             # Server-side TorqueScript (.cs files)
│       ├── game.cs          # Core game logic
│       ├── commands.cs      # Console commands
│       └── ...
├── testgame/               # Demo game world (REQUIRED for testing)
│   ├── zones/
│   │   ├── base.mis         # Base zone mission file ← CRITICAL
│   │   ├── landone.mis      # LandOne zone mission
│   │   ├── landtwo.mis      # LandTwo zone mission
│   │   └── ...
│   ├── world.db            # World database
│   ├── items/              # Item definitions
│   ├── mobs/               # Mob definitions
│   └── ...
└── data/                   # Game assets (for full client, can be minimal for server)
    ├── terrains/           # Terrain files (.ter)
    ├── shapes/             # 3D models (.dts)
    ├── textures/           # Textures (.png, .jpg)
    └── interiors/          # Interior files (.dif)
```

**Location**: `/home/user/MoMServer/minions.of.mirth/`

**Source**:
- Copy from Windows MoM installation: `%MOM_INSTALL%\minions.of.mirth\`
- Obtained from TMMOKit distribution

**Why needed**:
- `pytorque.Init()` looks for mission files in `$GAMEROOT/testgame/zones/*.mis`
- **If missing: zones hang on startup** (the exact issue you're experiencing)

**Copy from Windows**:
```bash
# On Windows machine
cd C:\Program Files (x86)\MinionsOfMirthUW
tar -czf minions.of.mirth.tar.gz minions.of.mirth/

# Transfer to Linux
scp minions.of.mirth.tar.gz user@linux-server:/home/user/MoMServer/

# On Linux
cd /home/user/MoMServer
tar -xzf minions.of.mirth.tar.gz
```

**Verification**:
```bash
ls -la minions.of.mirth/testgame/zones/*.mis
# Should show: base.mis, landone.mis, landtwo.mis, etc.
```

---

### 5. Common TGE Scripts (`common/`)

**Directory Structure**:
```
common/
├── server/
│   └── defaults.cs          # Default server settings
├── client/
│   └── defaults.cs          # Default client settings
└── main.cs                  # Common initialization
```

**Location**: `/home/user/MoMServer/common/`

**Source**: Copy from `%MOM_INSTALL%/common/`

**Why needed**: TGE loads shared scripts from here during initialization

**Copy**:
```bash
# From Windows MoM installation
scp -r "C:\Program Files (x86)\MinionsOfMirthUW\common" user@linux:/home/user/MoMServer/
```

**Verification**:
```bash
ls -la common/
```

---

### 6. Compiled TorqueScript (`main.cs.dso`)

**File**: `main.cs.dso`

**Location**: `/home/user/MoMServer/main.cs.dso`

**Source**: Copy from `%MOM_INSTALL%/main.cs.dso`

**Format**: DSO (Dynamically Shared Object) - pre-compiled TorqueScript

**Why needed**: TGE loads this as the main initialization script

**Copy**:
```bash
scp "C:\Program Files (x86)\MinionsOfMirthUW\main.cs.dso" user@linux:/home/user/MoMServer/
```

**Verification**:
```bash
ls -lh main.cs.dso
# Should be ~50-200 KB
```

---

### 7. Additional Libraries (Optional but Recommended)

**sqlobject/** - Database ORM
```
sqlobject/
├── __init__.py
├── sqlite/
└── ...
```

**Location**: `$MOM_INSTALL/library.zip` or extract to `$MOM_INSTALL/sqlobject/`

**Why needed**: Database access for characters, world data

---

## Step-by-Step Installation

### Scenario A: You Have a Windows MoM Installation

**Most common and easiest approach.**

#### Step 1: Set Up Environment

```bash
# On Linux server
export MOM_INSTALL=/opt/MinionsOfMirth
mkdir -p $MOM_INSTALL

# On Windows, set permanently:
# setx MOM_INSTALL "C:\Program Files (x86)\MinionsOfMirthUW"
# setx PYTHONPATH "%MOM_INSTALL%;%MOM_INSTALL%\library.zip"
```

#### Step 2: Copy Files from Windows to Linux

```bash
# On Windows machine, create archive
cd C:\Program Files (x86)\MinionsOfMirthUW
tar -czf mom-files.tar.gz common/ minions.of.mirth/ library.zip main.cs.dso

# Transfer to Linux
scp mom-files.tar.gz user@linux-server:/opt/

# On Linux, extract
cd /opt/MinionsOfMirth
tar -xzf /opt/mom-files.tar.gz
```

#### Step 3: Build or Copy TGE Binaries

**Option A - Linux**: Build from source (see `BUILD_TGE_FORK.md`)

**Option B - Windows Server**: Copy Windows binaries
```bash
# On Windows
copy pytge.pyd %MOM_INSTALL%\
copy tgenative.pyd %MOM_INSTALL%\
```

#### Step 4: Extract Python Modules

```bash
cd $MOM_INSTALL
unzip library.zip -d .
# This extracts mud/, sqlobject/, and other Python modules
```

#### Step 5: Run Install Script

```bash
cd /home/user/MoMServer

# Set environment (add to ~/.bashrc for persistence)
export MOM_INSTALL=/opt/MinionsOfMirth
export PYTHONPATH=$MOM_INSTALL:$MOM_INSTALL/library.zip:$PYTHONPATH

# Run Install.py (copies files to server directory)
python2.7 Install.py
```

#### Step 6: Verify Installation

```bash
python2.7 check_installation.py
```

All checks should pass.

---

### Scenario B: You Only Have This Repository (No MoM Installation)

**Difficult path - requires obtaining MoM or building everything from scratch.**

#### Option 1: Acquire Minions of Mirth

1. Find a copy of the Minions of Mirth game installer
2. Install on Windows (even in a VM)
3. Follow **Scenario A** above

#### Option 2: Use TMMOKit

1. Download TMMOKit 1.3 SP2 (the base this server uses)
2. Extract to `$MOM_INSTALL`
3. Build TGE bindings from TMMOKit's TGE source
4. Follow **Scenario A** steps 4-6

#### Option 3: Minimal Reconstruction (Advanced)

If you can't get MoM, you can try to reconstruct the minimum:

1. **Build pytge/tgenative** from tge-fork-152 (see `BUILD_TGE_FORK.md`)
2. **Create minimal mud module**:
   ```bash
   mkdir -p $MOM_INSTALL/mud/world
   mkdir -p $MOM_INSTALL/mud/simulation
   mkdir -p $MOM_INSTALL/mud/common

   # Create stub files (you'll need to reverse-engineer the APIs)
   touch $MOM_INSTALL/mud/__init__.py
   touch $MOM_INSTALL/mud/gamesettings.py
   # ... etc (very complex, not recommended)
   ```

3. **Create minimal mission files**:
   ```bash
   mkdir -p minions.of.mirth/testgame/zones
   # Create empty base.mis (won't work without proper TGE mission format)
   ```

**Reality**: This approach is **extremely difficult** and likely won't work without extensive TGE/MoM knowledge.

---

### Scenario C: Using tge-fork-152 Evaluation

If you're specifically evaluating tge-fork-152 integration:

#### Step 1: Obtain tge-fork-152

```bash
git clone <tge-fork-152-repo-url> ~/tge-fork-152
cd ~/tge-fork-152
```

#### Step 2: Check for Pre-built Binaries

```bash
find . -name "pytge.*" -o -name "tgenative.*"
# If found, copy to $MOM_INSTALL
```

#### Step 3: Check for Game Content

```bash
# Does tge-fork-152 include minions.of.mirth/?
ls -la minions.of.mirth/testgame/zones/

# Does it include mud module?
ls -la mud/
```

#### Step 4: Build if Necessary

Follow `BUILD_TGE_FORK.md` to build binaries.

#### Step 5: Copy Everything to $MOM_INSTALL

```bash
export MOM_INSTALL=/opt/MinionsOfMirth
mkdir -p $MOM_INSTALL

# Copy binaries
cp pytge.so tgenative.so $MOM_INSTALL/

# Copy game content (if included)
cp -r minions.of.mirth/ $MOM_INSTALL/
cp -r common/ $MOM_INSTALL/
cp -r mud/ $MOM_INSTALL/
```

#### Step 6: Test Integration

```bash
cd /home/user/MoMServer
python2.7 check_installation.py
```

---

## Verifying Installation

### Run Diagnostic

```bash
cd /home/user/MoMServer
python2.7 check_installation.py
```

**Expected output** (all OK):
```
✓ MOM_INSTALL: /opt/MinionsOfMirth
✓ PYTHONPATH: /opt/MinionsOfMirth:...
✓ common: Path: /home/user/MoMServer/common
✓ mud: Path: /home/user/MoMServer/mud
✓ minions.of.mirth: Path: /home/user/MoMServer/minions.of.mirth
✓ pytge: Found at /opt/MinionsOfMirth/pytge.so
✓ tgenative: Found at /opt/MinionsOfMirth/tgenative.so
✓ Mission files (.mis): 3 files found: base.mis, landone.mis, landtwo.mis
```

### Test TGE Initialization

```bash
cd /home/user/MoMServer
python2.7 << 'EOF'
import sys
import os

os.chdir('/home/user/MoMServer')
sys.argv = ['test', '-game', 'minions.of.mirth']

print("1. Testing imports...")
from mud.gamesettings import GAMEROOT
print("   GAMEROOT:", GAMEROOT)

import pytorque
print("   pytorque:", pytorque.__file__)

from tgenative import TGESetGlobal
print("   tgenative: OK")

print("\n2. Testing pytorque.Init()...")
print("   (This may take 5-30 seconds)")
pytorque.Init(sys.argv)
print("   SUCCESS!")

print("\n3. Testing pytorque.Tick()...")
for i in range(5):
    if not pytorque.Tick():
        print("   Tick failed!")
        break
    print("   Tick {} OK".format(i+1))

print("\n4. Shutting down...")
pytorque.Shutdown()
print("   SUCCESS - TGE integration working!")
EOF
```

**If this completes successfully**, your TGE integration is working and zones should start.

**If it hangs at step 2**, mission files are missing or corrupted.

---

## Troubleshooting Zone Startup

### Problem: "ImportError: No module named mud"

**Cause**: `mud` module not in PYTHONPATH

**Fix**:
```bash
# Check if mud exists
ls -la $MOM_INSTALL/mud/

# If missing, extract from library.zip
cd $MOM_INSTALL
unzip library.zip

# Verify PYTHONPATH
echo $PYTHONPATH
# Should include $MOM_INSTALL

# Add to environment
export PYTHONPATH=$MOM_INSTALL:$PYTHONPATH
```

---

### Problem: "ImportError: No module named pytge"

**Cause**: `pytge.so` not in PYTHONPATH or not built

**Fix**:
```bash
# Check if pytge.so exists
find $MOM_INSTALL -name "pytge.*"

# If missing on Linux, build from source
# See BUILD_TGE_FORK.md

# If missing on Windows, copy from MoM installation
copy "C:\Program Files (x86)\MinionsOfMirthUW\pytge.pyd" %MOM_INSTALL%\
```

---

### Problem: Zone Hangs at "Initialising pytorque"

**Cause**: `pytorque.Init()` blocking on mission file load

**Diagnosis**:
```bash
# Check if mission files exist
ls -la minions.of.mirth/testgame/zones/*.mis

# Check if main.cs.dso exists
ls -la main.cs.dso

# Check if common/ exists
ls -la common/
```

**Fix**:
```bash
# Copy missing files from MoM installation
scp -r "C:\...\MinionsOfMirthUW\minions.of.mirth" /home/user/MoMServer/
scp -r "C:\...\MinionsOfMirthUW\common" /home/user/MoMServer/
scp "C:\...\MinionsOfMirthUW\main.cs.dso" /home/user/MoMServer/
```

---

### Problem: "Zones never declare they're up"

**This is your current issue!**

**Cause**: One of these:
1. Zone process crashes on startup (check logs)
2. `pytorque.Init()` hangs (mission files missing)
3. Zone registers but callback fails (mud.world.theworld issue)

**Diagnosis**:
```bash
# Check if zone processes exist
ps aux | grep zoneserver
# Should show: python zoneserver.py -game minions.of.mirth ...

# Check zone logs
tail -f logs/ZoneCluster0.txt

# Manually test zone startup
python2.7 zoneserver.py -game minions.of.mirth -cluster=0 -dynamic
```

**Fix**: Based on error in logs:
- **ImportError**: Install missing modules
- **Hangs silently**: Mission files missing, copy from MoM
- **Segfault**: ABI mismatch, rebuild pytge.so for your Python version

---

### Problem: "Symbol not found" or "Undefined symbol"

**Cause**: TGE library dependencies missing

**Fix**:
```bash
# Check pytge dependencies
ldd pytge.so
# Look for "not found"

# Install missing libraries
# Ubuntu/Debian
sudo apt-get install libopenal1 libvorbisfile3 libgl1 libglu1

# Add TGE lib directory to LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$MOM_INSTALL/lib:$LD_LIBRARY_PATH
```

---

## Platform-Specific Notes

### Windows

**Easiest platform** - binaries come pre-built with MoM installation.

1. Install MoM and update it
2. Install Python 2.7, wxPython 2.8
3. Set environment variables
4. Run `Install.py`
5. Start servers

**No building required!**

---

### Linux

**More difficult** - must build TGE bindings from source.

**Requirements**:
- Build TGE from tge-fork-152 source (see `BUILD_TGE_FORK.md`)
- Copy game content from Windows MoM installation
- Set up environment variables

**Challenge**: Getting working `pytge.so` and `tgenative.so`

---

### macOS

**Similar to Linux** - must build from source.

**Additional notes**:
- Use `pythonw` instead of `python` for GUI apps
- Check `worldimp.py:93-105` for macOS-specific spawning code
- May need Xcode command-line tools

---

## Quick Reference: Minimum File Checklist

Use this checklist to verify you have everything:

```
Environment:
 [ ] MOM_INSTALL set and points to valid directory
 [ ] PYTHONPATH includes $MOM_INSTALL

TGE Binaries (platform-specific):
 [ ] pytge.so (Linux) or pytge.pyd (Windows)
 [ ] tgenative.so (Linux) or tgenative.pyd (Windows)

Python Modules:
 [ ] mud/ directory or library.zip
 [ ] sqlobject/ (for database access)

Game Content:
 [ ] minions.of.mirth/main.cs
 [ ] minions.of.mirth/testgame/zones/base.mis
 [ ] minions.of.mirth/testgame/zones/landone.mis
 [ ] common/ directory
 [ ] main.cs.dso

Server Files (from this repo):
 [ ] mud_ext/ directory
 [ ] projects/mom.cfg
 [ ] MasterServer.py, WorldServer.py, etc.

Verification:
 [ ] python check_installation.py shows all OK
 [ ] pytorque.Init() test completes without hanging
```

If all checkboxes are checked, zones should start successfully!

---

## Next Steps

After completing installation:

1. ✅ Run `python2.7 check_installation.py` - all checks pass
2. ✅ Test TGE initialization - no hangs
3. ✅ Create world using WorldManager
4. ✅ Start all servers in order:
   ```bash
   python2.7 MasterServer.py gameconfig=mom.cfg
   python2.7 GMServer.py gameconfig=mom.cfg
   python2.7 CharacterServer.py gameconfig=mom.cfg
   python2.7 WorldManager.py gameconfig=mom.cfg
   ```
5. ✅ Create a world in WorldManager GUI
6. ✅ Start WorldServer - zones should come up!
7. ✅ Connect with client and test

---

## Summary

**Why zones weren't starting:**
- Missing `mud` module → can't import game logic
- Missing `pytge.so` → can't initialize TGE
- Missing mission files → `pytorque.Init()` hangs
- Missing `common/` → TGE can't load scripts

**Solution:**
1. Set up `$MOM_INSTALL` with all required files
2. Build or copy TGE bindings (`pytge.so`)
3. Copy game content from MoM installation
4. Run `check_installation.py` to verify
5. Test TGE initialization
6. Start servers

**This is NOT a Linux abstraction issue** - it's simply missing the game engine and content that both Windows and Linux need.

The repository is designed to **augment** an existing MoM installation, not replace it. Think of this repo as the "server orchestration layer" that sits on top of the actual game engine (TGE) and game content (minions.of.mirth).
