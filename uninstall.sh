#!/bin/bash
# Uninstall script for NoxFeed

set -e

# Default variables
INSTALL_DIR="/home/nox/noxfeed"
SERVICE_NAME="noxfeed"
SERVICE_USER="nox"
TOKEN_FILE="/home/nox/.noxfeed_token"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo "NoxFeed Uninstall Script"
    echo ""
    echo "Usage: sudo ./uninstall.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --install-dir DIR   Installation directory (default: /home/nox/noxfeed)"
    echo "  --user USER         Service user (default: nox)"
    echo "  --service NAME      Service name (default: noxfeed)"
    echo "  --help, -h          Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo ./uninstall.sh"
    echo "  sudo ./uninstall.sh --install-dir /opt/myapp --user myuser"
    echo ""
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --user)
            SERVICE_USER="$2"
            TOKEN_FILE="/home/$2/.noxfeed_token"
            shift 2
            ;;
        --service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${RED}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║         NoxFeed Uninstall Script                       ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Service name:         $SERVICE_NAME"
echo "  Service user:         $SERVICE_USER"
echo "  Installation dir:     $INSTALL_DIR"
echo "  Token file:           $TOKEN_FILE"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}WARNING: This will remove the NoxFeed service and all its data!${NC}"
read -p "Are you sure you want to continue? (Type 'yes' to confirm): " -r
echo

if [ "$REPLY" != "yes" ]; then
    echo "Uninstall cancelled."
    exit 0
fi

# Stop service if running
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "Stopping $SERVICE_NAME service..."
    systemctl stop "$SERVICE_NAME"
fi

# Disable service
if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo "Disabling $SERVICE_NAME service..."
    systemctl disable "$SERVICE_NAME"
fi

# Remove systemd service file
if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    echo "Removing systemd service file..."
    rm "/etc/systemd/system/$SERVICE_NAME.service"
    systemctl daemon-reload
fi

# Ask about removing installation directory
if [ -d "$INSTALL_DIR" ]; then
    read -p "Remove installation directory $INSTALL_DIR? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing installation directory..."
        rm -rf "$INSTALL_DIR"
        echo -e "${GREEN}Installation directory removed.${NC}"
    else
        echo "Installation directory kept at: $INSTALL_DIR"
    fi
fi

# Ask about removing user and group
if id -u "$SERVICE_USER" >/dev/null 2>&1; then
    read -p "Remove user $SERVICE_USER? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing user $SERVICE_USER..."
        # userdel -r removes user and primary group, plus home directory
        userdel -r "$SERVICE_USER" 2>/dev/null || userdel "$SERVICE_USER"
        
        # Remove group if it still exists (in case it wasn't the primary group)
        if getent group "$SERVICE_USER" >/dev/null 2>&1; then
            groupdel "$SERVICE_USER" 2>/dev/null
        fi
        
        echo -e "${GREEN}User and group removed.${NC}"
    else
        echo "User $SERVICE_USER kept."
    fi
fi

# Ask about removing token
if [ -f "$TOKEN_FILE" ]; then
    read -p "Remove GitHub token file $TOKEN_FILE? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing token file..."
        rm "$TOKEN_FILE"
        echo -e "${GREEN}Token file removed.${NC}"
    else
        echo "Token file kept at: $TOKEN_FILE"
    fi
fi

echo ""
echo -e "${GREEN}Uninstall complete!${NC}"
echo ""
echo -e "${YELLOW}NOTE:${NC} System packages were NOT removed (they may be used by other applications):"
echo "  - python3, python3-venv"
echo "  - rtl-sdr, multimon-ng"
echo "  - git (if installed)"
echo ""
echo "If you want to remove them manually, run:"
echo "  sudo apt remove python3-venv rtl-sdr multimon-ng"
echo ""
