# MoM Server - Linux Testing Guide

This guide walks through testing the Wine-based Linux setup.

## Prerequisites Check

Before starting, verify you have network connectivity and the ability to install packages:

```bash
# Test network
ping -c 3 google.com

# Check if you can access package repos
sudo apt update

# Verify you have sudo access
sudo -v
```

## Wine Setup Testing (Preferred Method)

### Step 1: Install Wine Dependencies

```bash
# Enable 32-bit architecture (required for 32-bit Wine)
sudo dpkg --add-architecture i386

# Update package list
sudo apt update

# Install Wine and winetricks
sudo apt install wine64 wine32 winetricks -y

# Verify installation
wine --version
winetricks --version
```

Expected output:
- Wine version 8.0 or higher
- winetricks version info

### Step 2: Create Wine Environment

```bash
# Run the Wine environment setup script
cd /home/user/MoMServer
./setup-wine-env.sh
```

Expected behavior:
- Creates Wine prefix at `~/.wine-mom`
- Initializes 32-bit Wine environment
- Shows success message with next steps

Verify:
```bash
# Check Wine prefix exists
ls -la ~/.wine-mom/

# Should show drive_c directory and Wine registry files
```

### Step 3: Install Python 2.7

```bash
./install-python-wine.sh
```

Expected behavior:
- Downloads Python 2.7.18 MSI to `.downloads/`
- Installs Python to `C:\Python27` inside Wine
- Verifies installation by running `python --version`

Verify:
```bash
# Test Python in Wine
wine "C:\\Python27\\python.exe" --version

# Expected: Python 2.7.18
```

### Step 4: Install Dependencies

```bash
./install-dependencies-wine.sh
```

Expected behavior:
- Installs pip
- Installs Visual C++ Runtime via winetricks
- Downloads and installs wxPython 2.8.12.1
- Installs Python packages from requirements.txt
- Shows verification of critical imports

Verify each component:
```bash
# Test pip
wine "C:\\Python27\\python.exe" -m pip --version

# Test wxPython
wine "C:\\Python27\\python.exe" -c "import wx; print(wx.VERSION_STRING)"
# Expected: 2.8.12.1

# Test other packages
wine "C:\\Python27\\python.exe" -c "import twisted; print('Twisted OK')"
wine "C:\\Python27\\python.exe" -c "import Crypto; print('pycrypto OK')"
```

### Step 5: Test Server Wrapper Script

```bash
# Test help command
./run-mom-server.sh help

# Test Python command
./run-mom-server.sh python --version
# Expected: Python 2.7.18

# Test Python import
./run-mom-server.sh python -c "import sys; print(sys.path)"
```

## Known Issues and Troubleshooting

### Issue: Wine fails to initialize
**Symptoms:** Wine hangs or shows graphics errors

**Solutions:**
```bash
# Try running in virtual desktop mode
export WINEDLLOVERRIDES="winemenubuilder.exe=d"

# Or set Wine to not try to create desktop integration
winetricks settings nocrashdialog
```

### Issue: wxPython download fails
**Symptoms:** 404 error or timeout downloading wxPython

**Solutions:**
1. Manual download:
   ```bash
   # Download from alternative mirror
   wget https://sourceforge.net/projects/wxpython/files/wxPython/2.8.12.1/wxPython2.8-win32-unicode-2.8.12.1-py27.exe
   mv wxPython2.8-win32-unicode-2.8.12.1-py27.exe .downloads/
   ```
2. Retry installation script

### Issue: pip packages fail to install
**Symptoms:** Compilation errors, missing dependencies

**Solutions:**
```bash
# Install packages one at a time to identify problem
wine "C:\\Python27\\python.exe" -m pip install email==4.0.2
wine "C:\\Python27\\python.exe" -m pip install pyasn1==0.4.8
wine "C:\\Python27\\python.exe" -m pip install pycrypto==2.3
wine "C:\\Python27\\python.exe" -m pip install Twisted==10.1.0
wine "C:\\Python27\\python.exe" -m pip install zope.interface==5.2.0

# For pycrypto failures, try installing build dependencies
sudo apt install build-essential libgmp-dev
```

### Issue: MoM game files missing
**Symptoms:** Error about missing MinionsOfMirthUW directory

**Solutions:**
You need to obtain MoM game files. Options:
1. Copy from Windows installation
2. Extract from game installer
3. Ask user community for guidance

Place files in:
```bash
~/.wine-mom/drive_c/Program Files/MinionsOfMirthUW/
```

## Full Integration Test (Once Everything is Installed)

### Test 1: Run Install.py

```bash
./run-mom-server.sh install
```

Expected: Copies files from MoM installation, sets up server structure

### Test 2: Start Individual Server Components

Terminal 1:
```bash
./run-mom-server.sh master
```

Terminal 2:
```bash
./run-mom-server.sh gm
```

Terminal 3:
```bash
./run-mom-server.sh character
```

Terminal 4:
```bash
./run-mom-server.sh world-manager
```

Expected behavior:
- Each server starts without errors
- Master Server binds to port 2002
- GM Server binds to port 2003
- Character Server starts
- World Manager GUI opens (wxPython)

### Test 3: Start All Servers at Once

```bash
# Install tmux or screen first
sudo apt install tmux

# Start all servers
./run-mom-server.sh all

# Check status
./run-mom-server.sh status

# View logs
tmux attach -t mom-master
# (Ctrl+B, D to detach)

# Stop all servers
./run-mom-server.sh stop
```

### Test 4: Network Connectivity

```bash
# Check if Master Server is listening
netstat -tlnp | grep 2002

# Try connecting locally
telnet localhost 2002
```

## Performance Benchmarks

Record these metrics during testing:

1. **Startup Time:**
   - Time for Wine prefix creation: ______
   - Time for Python installation: ______
   - Time for dependencies installation: ______
   - Time for server startup: ______

2. **Resource Usage:**
   ```bash
   # Monitor while servers are running
   top -p $(pgrep -d',' -f "MasterServer.py|GMServer.py|CharacterServer.py")
   ```

3. **Network Latency:**
   - Test connection response time to Master Server
   - Test character creation/login

## Build from Source Alternative

If Wine approach fails or has unacceptable performance issues, document:

1. Which step failed?
2. What error messages occurred?
3. Wine version tested?
4. Resource usage (CPU/RAM)?

Then proceed to build-from-source approach documented in LINUX_SETUP.md.

## Success Criteria

✅ Wine prefix created successfully
✅ Python 2.7.18 runs in Wine
✅ wxPython imports without errors
✅ All pip packages install
✅ Install.py completes
✅ All four server components start
✅ World Manager GUI displays
✅ Client can connect to Master Server
✅ Can create account and character
✅ Can log into game world

## Reporting Results

When testing is complete, create a report with:

1. System info: `uname -a`, `wine --version`
2. Success/failure of each step
3. Any errors encountered
4. Performance observations
5. Recommendations for improvements

Save results to: `TESTING_RESULTS.md`
