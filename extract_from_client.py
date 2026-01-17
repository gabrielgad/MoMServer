#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract MoM Server Files from Client Installation

This script helps you extract all necessary files from your Minions of Mirth
client installation to set up a working server environment.

It will:
1. Detect your MoM client installation
2. Check architecture (32-bit vs 64-bit)
3. Extract all required files
4. Set up directory structure
5. Provide guidance on next steps
"""

import os
import sys
import shutil
import zipfile
import platform
import struct
from collections import OrderedDict

try:
    # Python 2/3 compatibility
    input = raw_input
except NameError:
    pass


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def colorize(text, color):
    if sys.stdout.isatty():
        return color + text + Colors.ENDC
    return text


def print_header(text):
    print("\n" + "="*70)
    print(colorize(text, Colors.HEADER + Colors.BOLD))
    print("="*70)


def find_mom_client():
    """Try to find MoM client installation automatically"""
    print_header("1. LOCATING MOM CLIENT INSTALLATION")

    possible_paths = []

    if platform.system() == 'Windows':
        # Common Windows installation paths
        possible_paths = [
            r"C:\Program Files (x86)\MinionsOfMirthUW",
            r"C:\Program Files\MinionsOfMirthUW",
            os.path.join(os.getenv('LocalAppData', ''), 'MinionsOfMirthUW'),
            os.path.join(os.getenv('ProgramFiles(x86)', ''), 'MinionsOfMirthUW'),
            os.path.join(os.getenv('ProgramFiles', ''), 'MinionsOfMirthUW'),
        ]
    else:
        # Linux/macOS paths (if Wine installation)
        home = os.path.expanduser('~')
        possible_paths = [
            os.path.join(home, '.wine', 'drive_c', 'Program Files (x86)', 'MinionsOfMirthUW'),
            os.path.join(home, '.wine', 'drive_c', 'Program Files', 'MinionsOfMirthUW'),
            '/opt/MinionsOfMirth',
            '/usr/local/MinionsOfMirth',
        ]

    found_paths = []
    for path in possible_paths:
        if os.path.exists(path):
            # Verify it looks like MoM installation
            if (os.path.exists(os.path.join(path, 'minions.of.mirth')) or
                os.path.exists(os.path.join(path, 'library.zip'))):
                found_paths.append(path)
                print(colorize("✓ Found:", Colors.OKGREEN), path)

    if not found_paths:
        print(colorize("✗ No MoM installation found automatically", Colors.WARNING))
        return None

    if len(found_paths) == 1:
        return found_paths[0]

    # Multiple found, ask user
    print("\nMultiple installations found:")
    for i, path in enumerate(found_paths, 1):
        print("  {}. {}".format(i, path))

    choice = input("\nSelect installation (1-{}): ".format(len(found_paths)))
    try:
        return found_paths[int(choice) - 1]
    except (ValueError, IndexError):
        return found_paths[0]


def check_architecture(mom_path):
    """Check if installation is 32-bit or 64-bit"""
    print_header("2. CHECKING ARCHITECTURE")

    python_bits = struct.calcsize("P") * 8
    print("Current Python: {}-bit".format(python_bits))
    print("System: {}".format(platform.machine()))

    # Check pytge architecture
    pytge_path = None
    for filename in ['pytge.pyd', 'pytge.so']:
        path = os.path.join(mom_path, filename)
        if os.path.exists(path):
            pytge_path = path
            break

    if not pytge_path:
        print(colorize("⚠ Warning: pytge binary not found in client", Colors.WARNING))
        return None

    print("\nFound: {}".format(pytge_path))

    # Try to determine architecture
    arch_info = {
        'path': pytge_path,
        'bits': None,
        'platform': None
    }

    if platform.system() == 'Windows':
        # On Windows, check PE header
        try:
            with open(pytge_path, 'rb') as f:
                # Read DOS header
                dos_header = f.read(64)
                if dos_header[:2] != b'MZ':
                    print("Not a valid PE file")
                    return arch_info

                # Get PE header offset
                pe_offset = struct.unpack('<I', dos_header[60:64])[0]
                f.seek(pe_offset)

                # Read PE signature
                pe_sig = f.read(4)
                if pe_sig != b'PE\x00\x00':
                    print("Not a valid PE file")
                    return arch_info

                # Read machine type
                machine = struct.unpack('<H', f.read(2))[0]

                if machine == 0x14c:  # IMAGE_FILE_MACHINE_I386
                    arch_info['bits'] = 32
                    arch_info['platform'] = 'Windows'
                    print(colorize("✓ Architecture: 32-bit Windows", Colors.OKGREEN))
                elif machine == 0x8664:  # IMAGE_FILE_MACHINE_AMD64
                    arch_info['bits'] = 64
                    arch_info['platform'] = 'Windows'
                    print(colorize("✓ Architecture: 64-bit Windows", Colors.OKGREEN))
                else:
                    print("Unknown machine type: 0x{:x}".format(machine))

        except Exception as e:
            print(colorize("Error checking architecture: {}".format(e), Colors.FAIL))

    else:
        # On Linux/Mac, use file command
        try:
            import subprocess
            result = subprocess.check_output(['file', pytge_path]).decode()
            print("file output:", result)

            if '32-bit' in result:
                arch_info['bits'] = 32
                arch_info['platform'] = 'Linux/Unix'
                print(colorize("✓ Architecture: 32-bit ELF", Colors.OKGREEN))
            elif '64-bit' in result:
                arch_info['bits'] = 64
                arch_info['platform'] = 'Linux/Unix'
                print(colorize("✓ Architecture: 64-bit ELF", Colors.OKGREEN))
        except Exception as e:
            print(colorize("Error checking architecture: {}".format(e), Colors.FAIL))

    # Check for mismatch
    if arch_info['bits']:
        if arch_info['bits'] != python_bits:
            print(colorize("\n⚠ WARNING: ARCHITECTURE MISMATCH!", Colors.FAIL + Colors.BOLD))
            print("  pytge is {}-bit, but Python is {}-bit".format(
                arch_info['bits'], python_bits))
            print("\n  This WILL cause zones to fail to start!")
            print("\n  Solutions:")
            print("    1. Install {}-bit Python to match pytge".format(arch_info['bits']))
            print("    2. Build {}-bit pytge to match Python".format(python_bits))
            print("    3. Use Wine to run {}-bit Windows binaries on Linux".format(arch_info['bits']))
        else:
            print(colorize("\n✓ Architecture matches Python!", Colors.OKGREEN))

    return arch_info


def extract_files(mom_path, dest_path):
    """Extract all necessary files from MoM client"""
    print_header("3. EXTRACTING FILES")

    if not os.path.exists(dest_path):
        os.makedirs(dest_path)

    extracted = OrderedDict()

    # Files to copy
    files_to_copy = [
        ('pytge.pyd', 'TGE Python binding (Windows)'),
        ('pytge.so', 'TGE Python binding (Linux)'),
        ('tgenative.pyd', 'TGE native functions (Windows)'),
        ('tgenative.so', 'TGE native functions (Linux)'),
        ('library.zip', 'Python modules (mud, sqlobject, etc.)'),
        ('main.cs.dso', 'Compiled TorqueScript'),
    ]

    # Directories to copy
    dirs_to_copy = [
        ('common', 'Common TGE scripts'),
        ('minions.of.mirth', 'Game content (GAMEROOT)'),
    ]

    print("\nCopying files...")
    for filename, description in files_to_copy:
        src = os.path.join(mom_path, filename)
        dst = os.path.join(dest_path, filename)

        if os.path.exists(src):
            try:
                shutil.copy2(src, dst)
                print(colorize("✓", Colors.OKGREEN), filename, "-", description)
                extracted[filename] = True
            except Exception as e:
                print(colorize("✗", Colors.FAIL), filename, "- Error:", str(e))
                extracted[filename] = False
        else:
            print(colorize("⊗", Colors.WARNING), filename, "- Not found (may not be needed)")
            extracted[filename] = None

    print("\nCopying directories...")
    for dirname, description in dirs_to_copy:
        src = os.path.join(mom_path, dirname)
        dst = os.path.join(dest_path, dirname)

        if os.path.exists(src):
            try:
                if os.path.exists(dst):
                    print("  Removing existing:", dst)
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(colorize("✓", Colors.OKGREEN), dirname, "-", description)
                extracted[dirname] = True
            except Exception as e:
                print(colorize("✗", Colors.FAIL), dirname, "- Error:", str(e))
                extracted[dirname] = False
        else:
            print(colorize("✗", Colors.FAIL), dirname, "- Not found (CRITICAL!)")
            extracted[dirname] = False

    return extracted


def extract_library_zip(dest_path):
    """Extract library.zip to get mud module"""
    print_header("4. EXTRACTING PYTHON MODULES")

    library_zip = os.path.join(dest_path, 'library.zip')

    if not os.path.exists(library_zip):
        print(colorize("✗ library.zip not found", Colors.FAIL))
        return False

    print("Extracting library.zip...")
    try:
        with zipfile.ZipFile(library_zip, 'r') as zf:
            # Extract specific modules
            modules_to_extract = ['mud/', 'sqlobject/']

            for module in modules_to_extract:
                members = [m for m in zf.namelist() if m.startswith(module)]
                if members:
                    print("  Extracting {}... ({} files)".format(module, len(members)))
                    zf.extractall(dest_path, members)
                    print(colorize("  ✓ {}".format(module), Colors.OKGREEN))
                else:
                    print(colorize("  ⊗ {} not found in library.zip".format(module), Colors.WARNING))

        return True
    except Exception as e:
        print(colorize("Error extracting library.zip: {}".format(e), Colors.FAIL))
        return False


def verify_mission_files(dest_path):
    """Verify mission files exist"""
    print_header("5. VERIFYING MISSION FILES")

    gameroot = os.path.join(dest_path, 'minions.of.mirth')
    zones_path = os.path.join(gameroot, 'testgame', 'zones')

    if not os.path.exists(zones_path):
        print(colorize("✗ testgame/zones directory not found!", Colors.FAIL))
        return False

    mission_files = [f for f in os.listdir(zones_path) if f.endswith('.mis')]

    if not mission_files:
        print(colorize("✗ No .mis files found!", Colors.FAIL))
        return False

    print(colorize("✓ Found {} mission files:".format(len(mission_files)), Colors.OKGREEN))
    for mis in sorted(mission_files)[:10]:  # Show first 10
        print("  -", mis)

    if len(mission_files) > 10:
        print("  ... and {} more".format(len(mission_files) - 10))

    return True


def generate_launch_script(dest_path, arch_info):
    """Generate a launch script with correct environment"""
    print_header("6. GENERATING LAUNCH SCRIPT")

    script_name = 'launch_server.sh' if platform.system() != 'Windows' else 'launch_server.bat'
    script_path = os.path.join(dest_path, '..', script_name)

    if platform.system() != 'Windows':
        # Bash script for Linux
        content = """#!/bin/bash
# MoM Server Launch Script
# Generated by extract_from_client.py

# Set MOM_INSTALL
export MOM_INSTALL="{install_path}"

# Set PYTHONPATH
export PYTHONPATH=$MOM_INSTALL:$MOM_INSTALL/library.zip:$PYTHONPATH

# Set library path for TGE binaries
export LD_LIBRARY_PATH=$MOM_INSTALL:$MOM_INSTALL/lib:$LD_LIBRARY_PATH

# Architecture info
# pytge: {arch_bits}-bit {arch_platform}
# Python: {python_bits}-bit

cd "$(dirname "$0")"

echo "Environment:"
echo "  MOM_INSTALL: $MOM_INSTALL"
echo "  PYTHONPATH: $PYTHONPATH"
echo ""

# Uncomment the server you want to run:
# python2.7 check_installation.py
# python2.7 MasterServer.py gameconfig=mom.cfg
# python2.7 GMServer.py gameconfig=mom.cfg
# python2.7 CharacterServer.py gameconfig=mom.cfg
# python2.7 WorldManager.py gameconfig=mom.cfg

echo "Edit this script to uncomment the server you want to run"
""".format(
            install_path=os.path.abspath(dest_path),
            arch_bits=arch_info.get('bits', 'unknown'),
            arch_platform=arch_info.get('platform', 'unknown'),
            python_bits=struct.calcsize("P") * 8
        )
    else:
        # Batch script for Windows
        content = """@echo off
REM MoM Server Launch Script
REM Generated by extract_from_client.py

set MOM_INSTALL={install_path}
set PYTHONPATH=%MOM_INSTALL%;%MOM_INSTALL%\\library.zip;%PYTHONPATH%

cd /d "%~dp0"

echo Environment:
echo   MOM_INSTALL: %MOM_INSTALL%
echo   PYTHONPATH: %PYTHONPATH%
echo.

REM Uncomment the server you want to run:
REM python check_installation.py
REM python MasterServer.py gameconfig=mom.cfg
REM python GMServer.py gameconfig=mom.cfg
REM python CharacterServer.py gameconfig=mom.cfg
REM python WorldManager.py gameconfig=mom.cfg

echo Edit this script to uncomment the server you want to run
pause
""".format(install_path=os.path.abspath(dest_path))

    try:
        with open(script_path, 'w') as f:
            f.write(content)

        if platform.system() != 'Windows':
            os.chmod(script_path, 0o755)

        print(colorize("✓ Created: {}".format(script_path), Colors.OKGREEN))
        return script_path
    except Exception as e:
        print(colorize("✗ Error creating script: {}".format(e), Colors.FAIL))
        return None


def print_next_steps(dest_path, arch_info, script_path):
    """Print summary and next steps"""
    print_header("SUMMARY & NEXT STEPS")

    python_bits = struct.calcsize("P") * 8
    pytge_bits = arch_info.get('bits')

    if pytge_bits and pytge_bits != python_bits:
        print(colorize("\n⚠ CRITICAL: ARCHITECTURE MISMATCH DETECTED!", Colors.FAIL + Colors.BOLD))
        print("\n  Your pytge is {}-bit, but Python is {}-bit".format(pytge_bits, python_bits))
        print("\n  Zones WILL NOT START until this is fixed!")
        print("\n  Choose ONE solution:")
        print("\n  Option 1: Install {}-bit Python".format(pytge_bits))
        if pytge_bits == 32:
            print("    # Ubuntu/Debian")
            print("    sudo dpkg --add-architecture i386")
            print("    sudo apt-get install python2.7:i386")
        print("\n  Option 2: Use Wine (if Windows pytge)")
        print("    wine python2.7 MasterServer.py gameconfig=mom.cfg")
        print("\n  Option 3: Build {}-bit pytge from source".format(python_bits))
        print("    See BUILD_TGE_FORK.md")
        print("\n  Option 4: Read ARCHITECTURE_MISMATCH.md for complete guide")
    else:
        print(colorize("\n✓ Architecture appears compatible!", Colors.OKGREEN))

    print("\n" + "="*70)
    print(colorize("FILES EXTRACTED TO:", Colors.BOLD))
    print("  {}".format(os.path.abspath(dest_path)))

    print("\n" + colorize("NEXT STEPS:", Colors.BOLD))
    print("\n1. Review extracted files:")
    print("   ls -la {}".format(dest_path))

    print("\n2. Run diagnostic:")
    print("   cd {}".format(os.path.dirname(os.path.abspath(dest_path))))
    if script_path:
        print("   # Edit {} to set environment".format(os.path.basename(script_path)))
        print("   source {}".format(script_path))
    print("   python2.7 check_installation.py")

    print("\n3. If architecture matches, run Install.py:")
    print("   python2.7 Install.py")

    print("\n4. Start servers:")
    print("   python2.7 MasterServer.py gameconfig=mom.cfg")
    print("   python2.7 GMServer.py gameconfig=mom.cfg")
    print("   python2.7 CharacterServer.py gameconfig=mom.cfg")
    print("   python2.7 WorldManager.py gameconfig=mom.cfg")

    print("\n5. Read documentation:")
    print("   - ARCHITECTURE_MISMATCH.md (if architecture mismatched)")
    print("   - MINIMAL_INSTALL.md (complete setup guide)")
    print("   - BUILD_TGE_FORK.md (if need to rebuild pytge)")

    print("\n" + "="*70 + "\n")


def main():
    print(colorize("""
╔══════════════════════════════════════════════════════════════════════╗
║      MoM Server Files Extraction Tool                                ║
║      Extract everything from your MoM client installation           ║
╚══════════════════════════════════════════════════════════════════════╝
    """, Colors.HEADER + Colors.BOLD))

    # Find MoM client
    mom_path = find_mom_client()

    if not mom_path:
        print("\nCouldn't find MoM installation automatically.")
        mom_path = input("Enter path to MoM client installation: ").strip('"\'')

        if not os.path.exists(mom_path):
            print(colorize("Error: Path does not exist!", Colors.FAIL))
            return 1

    print(colorize("\nUsing MoM installation:", Colors.OKGREEN))
    print("  {}".format(mom_path))

    # Check architecture
    arch_info = check_architecture(mom_path)

    # Get destination
    default_dest = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mom_extracted'))
    dest_input = input("\nExtract to [{}]: ".format(default_dest)).strip('"\'')
    dest_path = dest_input if dest_input else default_dest

    # Extract files
    extracted = extract_files(mom_path, dest_path)

    # Extract library.zip
    extract_library_zip(dest_path)

    # Verify mission files
    verify_mission_files(dest_path)

    # Generate launch script
    script_path = generate_launch_script(dest_path, arch_info)

    # Print next steps
    print_next_steps(dest_path, arch_info, script_path)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(colorize("\nFatal error: {}".format(e), Colors.FAIL))
        import traceback
        traceback.print_exc()
        sys.exit(1)
