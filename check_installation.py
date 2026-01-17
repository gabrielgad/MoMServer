#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MoM Server Installation Diagnostic Tool

This script checks for all required components needed to run the MoM Server,
particularly focusing on the tge-fork integration and zone server startup.

Run this before attempting to start any servers to identify missing components.
"""

import os
import sys
import imp
from collections import OrderedDict

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colorize(text, color):
    """Add color to text if terminal supports it"""
    if sys.stdout.isatty():
        return color + text + Colors.ENDC
    return text

def print_header(text):
    """Print a section header"""
    print("\n" + "="*70)
    print(colorize(text, Colors.HEADER + Colors.BOLD))
    print("="*70)

def print_result(check_name, status, details=""):
    """Print check result with color coding"""
    status_symbol = colorize("✓", Colors.OKGREEN) if status else colorize("✗", Colors.FAIL)
    status_text = colorize("OK", Colors.OKGREEN) if status else colorize("MISSING/FAILED", Colors.FAIL)

    print("{} {}: {}".format(status_symbol, check_name, status_text))
    if details:
        print("  " + details)

def check_environment_variables():
    """Check if required environment variables are set"""
    print_header("1. ENVIRONMENT VARIABLES")

    results = OrderedDict()

    # Check MOM_INSTALL
    mom_install = os.getenv('MOM_INSTALL')
    results['MOM_INSTALL'] = {
        'status': mom_install is not None,
        'value': mom_install if mom_install else "NOT SET",
        'critical': True
    }

    # Check PYTHONPATH
    pythonpath = os.getenv('PYTHONPATH')
    results['PYTHONPATH'] = {
        'status': pythonpath is not None,
        'value': pythonpath if pythonpath else "NOT SET",
        'critical': True
    }

    for var, info in results.items():
        print_result(var, info['status'], info['value'])

    return results

def check_directories():
    """Check if required directories exist"""
    print_header("2. REQUIRED DIRECTORIES")

    server_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(server_root)

    required_dirs = OrderedDict([
        ('common', {
            'path': './common',
            'description': 'Common TGE scripts and configuration',
            'critical': True,
            'source': '$MOM_INSTALL/common/'
        }),
        ('mud', {
            'path': './mud',
            'description': 'Core game logic Python module',
            'critical': True,
            'source': '$MOM_INSTALL/library.zip or $MOM_INSTALL/mud/'
        }),
        ('minions.of.mirth', {
            'path': './minions.of.mirth',
            'description': 'Game content directory (GAMEROOT)',
            'critical': True,
            'source': '$MOM_INSTALL/minions.of.mirth/'
        }),
        ('sqlobject', {
            'path': './sqlobject',
            'description': 'SQLObject ORM library',
            'critical': True,
            'source': '$MOM_INSTALL/library.zip'
        }),
        ('mud_ext', {
            'path': './mud_ext',
            'description': 'Server extensions (should exist)',
            'critical': True,
            'source': 'Part of this repository'
        }),
        ('projects', {
            'path': './projects',
            'description': 'Project configuration files',
            'critical': True,
            'source': 'Part of this repository'
        }),
        ('serverconfig', {
            'path': './serverconfig',
            'description': 'Server configuration directory',
            'critical': False,
            'source': 'Created by WorldManager'
        })
    ])

    results = OrderedDict()
    for name, info in required_dirs.items():
        exists = os.path.exists(info['path']) and os.path.isdir(info['path'])
        results[name] = {
            'status': exists,
            'path': os.path.abspath(info['path']),
            'critical': info['critical']
        }

        detail = "Path: {} | Source: {}".format(
            os.path.abspath(info['path']),
            info['source']
        )
        print_result(name, exists, detail)

    return results

def check_files():
    """Check if required files exist"""
    print_header("3. REQUIRED FILES")

    required_files = OrderedDict([
        ('main.cs.dso', {
            'path': './main.cs.dso',
            'description': 'Compiled TorqueScript initialization',
            'critical': True,
            'source': '$MOM_INSTALL/main.cs.dso'
        }),
        ('projects/mom.cfg', {
            'path': './projects/mom.cfg',
            'description': 'Main game configuration',
            'critical': True,
            'source': 'Part of this repository'
        })
    ])

    results = OrderedDict()
    for name, info in required_files.items():
        exists = os.path.exists(info['path']) and os.path.isfile(info['path'])
        results[name] = {
            'status': exists,
            'path': os.path.abspath(info['path']),
            'critical': info['critical']
        }

        detail = "Path: {} | Source: {}".format(
            os.path.abspath(info['path']),
            info['source']
        )
        print_result(name, exists, detail)

    return results

def check_python_modules():
    """Check if required Python modules can be imported"""
    print_header("4. PYTHON MODULE IMPORTS")

    results = OrderedDict()

    # Check standard requirements
    standard_modules = [
        'twisted',
        'Crypto',
        'pyasn1',
        'zope.interface',
        'sqlobject'
    ]

    print(colorize("\n4.1 Standard Python Dependencies:", Colors.OKBLUE))
    for module_name in standard_modules:
        try:
            __import__(module_name)
            results[module_name] = {'status': True, 'error': None}
            print_result(module_name, True)
        except ImportError as e:
            results[module_name] = {'status': False, 'error': str(e)}
            print_result(module_name, False, str(e))

    # Check game-specific modules
    print(colorize("\n4.2 Game-Specific Modules (from MOM_INSTALL):", Colors.OKBLUE))

    game_modules = OrderedDict([
        ('mud', 'Core game logic module'),
        ('pytge', 'Python-TGE bindings (pytge.so/pyd)'),
        ('tgenative', 'TGE native functions (tgenative.so/pyd)')
    ])

    for module_name, description in game_modules.items():
        try:
            mod = __import__(module_name)
            module_file = getattr(mod, '__file__', 'built-in')
            results[module_name] = {
                'status': True,
                'path': module_file,
                'error': None
            }
            print_result(module_name, True, "Found at: {}".format(module_file))
        except ImportError as e:
            results[module_name] = {
                'status': False,
                'path': None,
                'error': str(e)
            }
            print_result(module_name, False, "{} - {}".format(description, str(e)))

    return results

def check_mud_submodules():
    """Check if mud submodules can be imported (only if mud exists)"""
    print_header("5. MUD SUBMODULE STRUCTURE")

    results = OrderedDict()

    try:
        import mud
        print(colorize("mud module found at: {}".format(mud.__file__), Colors.OKGREEN))

        submodules = OrderedDict([
            ('mud.gamesettings', 'Game configuration settings'),
            ('mud.world.theworld', 'World management class'),
            ('mud.world.zone', 'Zone management'),
            ('mud.world.core', 'Core world functions'),
            ('mud.simulation.simmind', 'Simulation mind / zone player tracking'),
            ('mud.common.dbconfig', 'Database configuration'),
            ('mud.utils', 'Utility functions')
        ])

        for module_name, description in submodules.items():
            try:
                parts = module_name.split('.')
                mod = __import__(module_name)
                for part in parts[1:]:
                    mod = getattr(mod, part)

                module_file = getattr(mod, '__file__', 'built-in')
                results[module_name] = {
                    'status': True,
                    'path': module_file
                }
                print_result(module_name, True, description)
            except (ImportError, AttributeError) as e:
                results[module_name] = {
                    'status': False,
                    'error': str(e)
                }
                print_result(module_name, False, str(e))

    except ImportError as e:
        print(colorize("Cannot check mud submodules - mud module not available", Colors.WARNING))
        print("Error: {}".format(e))
        results['_mud_unavailable'] = True

    return results

def check_tge_binaries():
    """Check for TGE binary modules with detailed platform info"""
    print_header("6. TGE NATIVE BINARIES")

    results = OrderedDict()
    platform = sys.platform

    print("Current platform: {}".format(platform))
    print("Python version: {}".format(sys.version))

    if platform == 'win32':
        expected_ext = '.pyd'
        binary_names = ['pytge.pyd', 'tgenative.pyd']
    else:
        expected_ext = '.so'
        binary_names = ['pytge.so', 'tgenative.so']

    print("\nExpected binary extension: {}".format(expected_ext))
    print("Searching in sys.path...\n")

    for binary in binary_names:
        found = False
        found_path = None

        # Search in PYTHONPATH / sys.path
        for path in sys.path:
            potential_path = os.path.join(path, binary)
            if os.path.exists(potential_path):
                found = True
                found_path = potential_path
                break

        results[binary] = {
            'status': found,
            'path': found_path
        }

        if found:
            size = os.path.getsize(found_path)
            print_result(binary, True, "Found at: {} ({} bytes)".format(found_path, size))
        else:
            print_result(binary, False, "Not found in PYTHONPATH")
            if platform != 'win32':
                print(colorize("  NOTE: On Linux, you must BUILD this from tge-fork-152 source", Colors.WARNING))

    return results

def check_mission_files():
    """Check for mission files in GAMEROOT"""
    print_header("7. GAME CONTENT (Mission Files)")

    results = OrderedDict()
    gameroot = './minions.of.mirth'

    if not os.path.exists(gameroot):
        print(colorize("GAMEROOT directory ({}) does not exist!".format(gameroot), Colors.FAIL))
        print("Cannot check for mission files.")
        results['_gameroot_missing'] = True
        return results

    # Check for testgame
    testgame_path = os.path.join(gameroot, 'testgame')
    results['testgame_dir'] = {
        'status': os.path.exists(testgame_path),
        'path': testgame_path
    }
    print_result('testgame directory', results['testgame_dir']['status'], testgame_path)

    if not results['testgame_dir']['status']:
        print(colorize("testgame directory missing - no demo game content", Colors.WARNING))
        return results

    # Check for zones
    zones_path = os.path.join(testgame_path, 'zones')
    results['zones_dir'] = {
        'status': os.path.exists(zones_path),
        'path': zones_path
    }
    print_result('zones directory', results['zones_dir']['status'], zones_path)

    if results['zones_dir']['status']:
        # Look for .mis files
        mission_files = [f for f in os.listdir(zones_path) if f.endswith('.mis')]
        results['mission_files'] = {
            'status': len(mission_files) > 0,
            'count': len(mission_files),
            'files': mission_files
        }

        if mission_files:
            print_result('Mission files (.mis)', True, "{} files found: {}".format(
                len(mission_files), ', '.join(mission_files[:5])
            ))
        else:
            print_result('Mission files (.mis)', False, "No .mis files found in zones directory")

    return results

def check_database_files():
    """Check for database files"""
    print_header("8. DATABASE FILES")

    results = OrderedDict()

    db_files = OrderedDict([
        ('Master DB', './master.db'),
        ('Character DB', './character.db'),
        ('World DB', './testgame/world.db')
    ])

    for name, path in db_files.items():
        exists = os.path.exists(path)
        results[name] = {
            'status': exists,
            'path': os.path.abspath(path)
        }

        if exists:
            size = os.path.getsize(path)
            print_result(name, True, "{} ({} bytes)".format(path, size))
        else:
            print_result(name, False, "{} - Will be created by Install.py or servers".format(path))

    return results

def check_install_py_status():
    """Check if Install.py has been run"""
    print_header("9. INSTALLATION STATUS")

    # Install.py copies these items
    install_indicators = [
        './common',
        './minions.of.mirth',
        './main.cs.dso'
    ]

    installed_count = sum(1 for path in install_indicators if os.path.exists(path))

    if installed_count == 0:
        print(colorize("✗ Install.py has NOT been run", Colors.FAIL))
        print("\n  Install.py copies critical files from MOM_INSTALL:")
        print("    - common/")
        print("    - minions.of.mirth/ (GAMEROOT)")
        print("    - main.cs.dso")
        print("\n  You must:")
        print("    1. Set MOM_INSTALL environment variable")
        print("    2. Run: python Install.py")
        return {'status': False}
    elif installed_count == len(install_indicators):
        print(colorize("✓ Install.py appears to have been run successfully", Colors.OKGREEN))
        return {'status': True}
    else:
        print(colorize("⚠ Install.py may have been partially run", Colors.WARNING))
        print("  {}/{} expected items found".format(installed_count, len(install_indicators)))
        return {'status': 'partial'}

def generate_summary(all_results):
    """Generate final summary and recommendations"""
    print_header("SUMMARY & RECOMMENDATIONS")

    critical_failures = []
    warnings = []

    # Analyze environment
    env_vars = all_results.get('environment', {})
    if not env_vars.get('MOM_INSTALL', {}).get('status'):
        critical_failures.append("MOM_INSTALL environment variable not set")
    if not env_vars.get('PYTHONPATH', {}).get('status'):
        critical_failures.append("PYTHONPATH environment variable not set")

    # Analyze directories
    dirs = all_results.get('directories', {})
    for name, info in dirs.items():
        if info.get('critical') and not info.get('status'):
            critical_failures.append("Missing directory: {}".format(name))

    # Analyze modules
    modules = all_results.get('modules', {})
    if not modules.get('mud', {}).get('status'):
        critical_failures.append("mud module not importable - core game logic missing")
    if not modules.get('pytge', {}).get('status'):
        critical_failures.append("pytge module not importable - TGE engine bindings missing")
    if not modules.get('tgenative', {}).get('status'):
        critical_failures.append("tgenative module not importable - TGE native functions missing")

    # Print summary
    if not critical_failures:
        print(colorize("\n✓ ALL CRITICAL COMPONENTS PRESENT", Colors.OKGREEN + Colors.BOLD))
        print("\nYour installation appears complete. You should be able to start servers.")
    else:
        print(colorize("\n✗ CRITICAL FAILURES DETECTED", Colors.FAIL + Colors.BOLD))
        print("\nThe following critical components are missing:\n")
        for i, failure in enumerate(critical_failures, 1):
            print("  {}. {}".format(i, colorize(failure, Colors.FAIL)))

        print(colorize("\n" + "="*70, Colors.BOLD))
        print(colorize("NEXT STEPS:", Colors.HEADER + Colors.BOLD))
        print("="*70)

        print("\n1. ENVIRONMENT SETUP:")
        print("   export MOM_INSTALL=/path/to/MinionsOfMirthUW")
        print("   export PYTHONPATH=$MOM_INSTALL:$MOM_INSTALL/library.zip")

        print("\n2. FOR LINUX - BUILD TGE BINARIES:")
        print("   See BUILD_TGE_FORK.md for complete instructions")
        print("   - Clone tge-fork-152 source")
        print("   - Build pytge.so and tgenative.so")
        print("   - Copy to $MOM_INSTALL")

        print("\n3. RUN INSTALL SCRIPT:")
        print("   python Install.py")
        print("   (This copies common/, minions.of.mirth/, main.cs.dso)")

        print("\n4. VERIFY INSTALLATION:")
        print("   python check_installation.py")

        print(colorize("\n" + "="*70, Colors.BOLD))

    if warnings:
        print(colorize("\nWARNINGS:", Colors.WARNING))
        for warning in warnings:
            print("  - {}".format(warning))

def main():
    """Main diagnostic routine"""
    print(colorize("""
╔══════════════════════════════════════════════════════════════════════╗
║     MoM Server Installation Diagnostic Tool                          ║
║     Checking tge-fork-152 Integration & Zone Server Requirements    ║
╚══════════════════════════════════════════════════════════════════════╝
    """, Colors.HEADER + Colors.BOLD))

    all_results = {}

    # Run all checks
    all_results['environment'] = check_environment_variables()
    all_results['directories'] = check_directories()
    all_results['files'] = check_files()
    all_results['modules'] = check_python_modules()
    all_results['mud_submodules'] = check_mud_submodules()
    all_results['tge_binaries'] = check_tge_binaries()
    all_results['mission_files'] = check_mission_files()
    all_results['databases'] = check_database_files()
    all_results['install_status'] = check_install_py_status()

    # Generate summary
    generate_summary(all_results)

    print("\n")

if __name__ == '__main__':
    main()
