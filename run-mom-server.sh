#!/bin/bash
# Wrapper script for running Minions of Mirth Server components through Wine

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WINE_PREFIX="${HOME}/.wine-mom"

export WINEPREFIX="$WINE_PREFIX"
export WINEARCH=win32

# MoM environment variables (Windows paths for Wine)
export MOM_INSTALL="C:\\Program Files\\MinionsOfMirthUW"
export PYTHONPATH="C:\\Python27\\Lib\\site-packages;$MOM_INSTALL;$MOM_INSTALL\\library.zip;"

# Python executable through Wine
PYTHON="wine C:\\Python27\\python.exe"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Wine prefix exists
check_wine_prefix() {
    if [ ! -d "$WINE_PREFIX" ]; then
        print_error "Wine prefix not found at $WINE_PREFIX"
        print_info "Please run ./setup-wine-env.sh first"
        exit 1
    fi
}

# Function to check if Python is installed
check_python() {
    if ! $PYTHON --version 2>&1 | grep -q "Python 2.7"; then
        print_error "Python 2.7 not found in Wine"
        print_info "Please run ./install-python-wine.sh first"
        exit 1
    fi
}

# Function to check if MoM files exist
check_mom_files() {
    # Check if MoM directory exists in Wine prefix
    MOM_DIR="$WINE_PREFIX/drive_c/Program Files/MinionsOfMirthUW"

    if [ ! -d "$MOM_DIR" ]; then
        print_warn "MoM game files not found at: $MOM_DIR"
        print_info "You need to install or copy Minions of Mirth game files."
        print_info "See LINUX_SETUP.md for instructions."
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Function to display usage
show_usage() {
    cat << EOF
Minions of Mirth Server - Wine Wrapper Script

Usage: $0 <command>

Commands:
    install         Run Install.py to set up the server
    master          Start the Master Server
    gm              Start the GM Server
    character       Start the Character Server
    world-manager   Start the World Manager (GUI)
    world-daemon    Start a World Daemon
    client          Start the game client
    all             Start all servers (master, gm, character) in background
    stop            Stop all running servers
    status          Show status of running servers
    python          Run Python interpreter in Wine
    help            Show this help message

Examples:
    $0 install                 # Run initial installation
    $0 master                  # Start Master Server
    $0 all                     # Start all servers
    $0 python -c "import wx"  # Test wxPython import

Environment:
    WINE_PREFIX: $WINE_PREFIX
    MOM_INSTALL: $MOM_INSTALL
    PYTHONPATH:  $PYTHONPATH

EOF
}

# Main script logic
case "$1" in
    install)
        print_info "Running Install.py..."
        check_wine_prefix
        check_python
        cd "$SCRIPT_DIR"
        $PYTHON Install.py
        ;;

    master)
        print_info "Starting Master Server..."
        check_wine_prefix
        check_python
        check_mom_files
        cd "$SCRIPT_DIR"
        $PYTHON MasterServer.py gameconfig=mom.cfg
        ;;

    gm)
        print_info "Starting GM Server..."
        check_wine_prefix
        check_python
        check_mom_files
        cd "$SCRIPT_DIR"
        $PYTHON GMServer.py gameconfig=mom.cfg
        ;;

    character)
        print_info "Starting Character Server..."
        check_wine_prefix
        check_python
        check_mom_files
        cd "$SCRIPT_DIR"
        $PYTHON CharacterServer.py gameconfig=mom.cfg
        ;;

    world-manager)
        print_info "Starting World Manager..."
        check_wine_prefix
        check_python
        check_mom_files
        cd "$SCRIPT_DIR"
        $PYTHON WorldManager.py gameconfig=mom.cfg
        ;;

    world-daemon)
        print_info "Starting World Daemon..."
        check_wine_prefix
        check_python
        check_mom_files
        cd "$SCRIPT_DIR"
        if [ -z "$2" ]; then
            print_error "World name required"
            print_info "Usage: $0 world-daemon <world_name>"
            exit 1
        fi
        $PYTHON WorldDaemon.py gameconfig=mom.cfg world=$2
        ;;

    client)
        print_info "Starting Client..."
        check_wine_prefix
        check_python
        check_mom_files
        cd "$SCRIPT_DIR"
        $PYTHON Client.pyw
        ;;

    all)
        print_info "Starting all servers..."
        check_wine_prefix
        check_python
        check_mom_files

        # Check if screen or tmux is available
        if command -v tmux &> /dev/null; then
            print_info "Using tmux to manage servers"
            tmux new-session -d -s mom-master "$0 master"
            sleep 2
            tmux new-session -d -s mom-gm "$0 gm"
            sleep 2
            tmux new-session -d -s mom-character "$0 character"
            sleep 2
            tmux new-session -d -s mom-world "$0 world-manager"

            print_info "All servers started in tmux sessions"
            print_info "Use 'tmux ls' to list sessions"
            print_info "Use 'tmux attach -t mom-master' to attach to a session"
            print_info "Use '$0 stop' to stop all servers"

        elif command -v screen &> /dev/null; then
            print_info "Using screen to manage servers"
            screen -dmS mom-master bash -c "$0 master"
            sleep 2
            screen -dmS mom-gm bash -c "$0 gm"
            sleep 2
            screen -dmS mom-character bash -c "$0 character"
            sleep 2
            screen -dmS mom-world bash -c "$0 world-manager"

            print_info "All servers started in screen sessions"
            print_info "Use 'screen -ls' to list sessions"
            print_info "Use 'screen -r mom-master' to attach to a session"
            print_info "Use '$0 stop' to stop all servers"

        else
            print_error "Neither tmux nor screen is installed"
            print_info "Please install tmux or screen, or start servers manually in separate terminals:"
            print_info "  $0 master"
            print_info "  $0 gm"
            print_info "  $0 character"
            print_info "  $0 world-manager"
            exit 1
        fi
        ;;

    stop)
        print_info "Stopping all servers..."

        if command -v tmux &> /dev/null; then
            tmux kill-session -t mom-master 2>/dev/null && print_info "Stopped Master Server" || true
            tmux kill-session -t mom-gm 2>/dev/null && print_info "Stopped GM Server" || true
            tmux kill-session -t mom-character 2>/dev/null && print_info "Stopped Character Server" || true
            tmux kill-session -t mom-world 2>/dev/null && print_info "Stopped World Manager" || true
        elif command -v screen &> /dev/null; then
            screen -S mom-master -X quit 2>/dev/null && print_info "Stopped Master Server" || true
            screen -S mom-gm -X quit 2>/dev/null && print_info "Stopped GM Server" || true
            screen -S mom-character -X quit 2>/dev/null && print_info "Stopped Character Server" || true
            screen -S mom-world -X quit 2>/dev/null && print_info "Stopped World Manager" || true
        fi

        # Also try to kill any Python processes running the servers
        pkill -f "MasterServer.py" 2>/dev/null && print_info "Killed MasterServer.py process" || true
        pkill -f "GMServer.py" 2>/dev/null && print_info "Killed GMServer.py process" || true
        pkill -f "CharacterServer.py" 2>/dev/null && print_info "Killed CharacterServer.py process" || true
        pkill -f "WorldManager.py" 2>/dev/null && print_info "Killed WorldManager.py process" || true

        print_info "All servers stopped"
        ;;

    status)
        print_info "Server Status:"
        echo ""

        if command -v tmux &> /dev/null; then
            tmux ls 2>/dev/null | grep "mom-" || print_info "No tmux sessions found"
        elif command -v screen &> /dev/null; then
            screen -ls | grep "mom-" || print_info "No screen sessions found"
        fi

        echo ""
        print_info "Python processes:"
        ps aux | grep -E "(MasterServer|GMServer|CharacterServer|WorldManager|WorldDaemon)" | grep -v grep || print_info "No server processes found"
        ;;

    python)
        check_wine_prefix
        check_python
        shift  # Remove 'python' from arguments
        cd "$SCRIPT_DIR"
        $PYTHON "$@"
        ;;

    help|--help|-h|"")
        show_usage
        ;;

    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
