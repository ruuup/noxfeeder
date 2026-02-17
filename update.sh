#!/bin/bash
# Update script for NoxFeed

set -e

# ===== DEFAULT CONFIGURATION =====
REPO_BRANCH="main"
INSTALL_DIR="/home/nox/noxfeed"
SERVICE_NAME="noxfeed"
SERVICE_USER="nox"
TOKEN_FILE="/home/nox/.noxfeed_token"
# =================================

VENV_DIR="$INSTALL_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo "NoxFeed Update Script"
    echo ""
    echo "Usage: sudo ./update.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --install-dir DIR   Installation directory (default: /home/nox/noxfeed)"
    echo "  --user USER         Service user (default: nox)"
    echo "  --service NAME      Service name (default: noxfeed)"
    echo "  --branch BRANCH     Git branch to pull (default: main)"
    echo "  --help, -h          Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo ./update.sh"
    echo "  sudo ./update.sh --branch develop"
    echo "  sudo ./update.sh --install-dir /opt/myapp --user myuser"
    echo ""
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --install-dir)
            INSTALL_DIR="$2"
            VENV_DIR="$INSTALL_DIR/venv"
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
        --branch)
            REPO_BRANCH="$2"
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

# Recalculate paths based on parsed arguments
BACKUP_DIR="${INSTALL_DIR}_backup_$(date +%Y%m%d_%H%M%S)"

echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         NoxFeed Update Script                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Service name:         $SERVICE_NAME"
echo "  Service user:         $SERVICE_USER"
echo "  Installation dir:     $INSTALL_DIR"
echo "  Git branch:           $REPO_BRANCH"
echo "  Token file:           $TOKEN_FILE"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

# Check if installation exists
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}Installation directory not found: $INSTALL_DIR${NC}"
    echo "Please run the installation script first."
    exit 1
fi

# Check if service exists
if ! systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
    echo -e "${YELLOW}Warning: Service $SERVICE_NAME not found in systemd${NC}"
fi

# Get GitHub token
GITHUB_TOKEN=""

if [ -f "$TOKEN_FILE" ]; then
    GITHUB_TOKEN=$(cat "$TOKEN_FILE")
    echo -e "${GREEN}Using saved GitHub token.${NC}"
else
    echo "GitHub token not found."
    echo "Please enter your GitHub Personal Access Token:"
    read -s GITHUB_TOKEN
    echo ""
    
    if [ -z "$GITHUB_TOKEN" ]; then
        echo -e "${RED}No token provided. Exiting.${NC}"
        exit 1
    fi
    
    # Save token for future use
    echo "$GITHUB_TOKEN" > "$TOKEN_FILE"
    chmod 600 "$TOKEN_FILE"
    chown "$SERVICE_USER:$SERVICE_USER" "$TOKEN_FILE"
    echo -e "${GREEN}Token saved to $TOKEN_FILE${NC}"
fi

# Check if service is running
SERVICE_WAS_RUNNING=false
if systemctl is-active --quiet "$SERVICE_NAME"; then
    SERVICE_WAS_RUNNING=true
    echo -e "${BLUE}Stopping $SERVICE_NAME service...${NC}"
    systemctl stop "$SERVICE_NAME"
    echo -e "${GREEN}Service stopped.${NC}"
else
    echo "Service is not running."
fi

# Create backup of current installation
echo -e "${BLUE}Creating backup...${NC}"
cp -r "$INSTALL_DIR" "$BACKUP_DIR"
echo -e "${GREEN}Backup created at: $BACKUP_DIR${NC}"

# Create backup of config
if [ -f "$INSTALL_DIR/config/config.json" ]; then
    cp "$INSTALL_DIR/config/config.json" "/tmp/noxfeed_config_backup.json"
    echo "Config backed up to /tmp/noxfeed_config_backup.json"
fi

# Update repository
echo -e "${BLUE}Updating repository...${NC}"
cd "$INSTALL_DIR"

# Configure git to use token
sudo -u "$SERVICE_USER" git config credential.helper store
echo "https://${GITHUB_TOKEN}@github.com" | sudo -u "$SERVICE_USER" git credential approve

# Stash any local changes
if sudo -u "$SERVICE_USER" git diff-index --quiet HEAD --; then
    echo "No local changes to stash."
else
    echo -e "${YELLOW}Stashing local changes...${NC}"
    sudo -u "$SERVICE_USER" git stash
fi

# Pull latest changes
echo "Pulling latest changes from repository (branch: $REPO_BRANCH)..."
sudo -u "$SERVICE_USER" git pull origin "$REPO_BRANCH"

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to pull changes from repository.${NC}"
    echo "Restoring from backup..."
    rm -rf "$INSTALL_DIR"
    cp -r "$BACKUP_DIR" "$INSTALL_DIR"
    
    if [ "$SERVICE_WAS_RUNNING" = true ]; then
        systemctl start "$SERVICE_NAME"
    fi
    
    echo -e "${RED}Update failed. Installation restored from backup.${NC}"
    exit 1
fi

echo -e "${GREEN}Repository updated successfully.${NC}"

# Restore config if it was backed up
if [ -f "/tmp/noxfeed_config_backup.json" ]; then
    echo "Restoring config..."
    cp "/tmp/noxfeed_config_backup.json" "$INSTALL_DIR/config/config.json"
    rm "/tmp/noxfeed_config_backup.json"
fi

# Update virtual environment if requirements changed
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    echo -e "${BLUE}Updating Python dependencies...${NC}"
    sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install --upgrade pip
    sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt" --upgrade
    echo -e "${GREEN}Dependencies updated.${NC}"
fi

# Set ownership
echo "Setting ownership..."
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Reload systemd if service file changed
if [ -f "$INSTALL_DIR/$SERVICE_NAME.service" ]; then
    echo "Updating systemd service file..."
    cp "$INSTALL_DIR/$SERVICE_NAME.service" "/etc/systemd/system/$SERVICE_NAME.service"
    systemctl daemon-reload
    echo -e "${GREEN}Systemd service file updated.${NC}"
fi

# Start service if it was running before
if [ "$SERVICE_WAS_RUNNING" = true ]; then
    echo -e "${BLUE}Starting $SERVICE_NAME service...${NC}"
    systemctl start "$SERVICE_NAME"
    
    # Wait a moment and check status
    sleep 2
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}Service started successfully.${NC}"
    else
        echo -e "${RED}Service failed to start. Check logs with: journalctl -u $SERVICE_NAME -n 50${NC}"
        echo "You can restore from backup: $BACKUP_DIR"
        exit 1
    fi
else
    echo -e "${YELLOW}Service was not running before update. Not starting it automatically.${NC}"
    echo "You can start it manually with: sudo systemctl start $SERVICE_NAME"
fi

echo ""
echo -e "${GREEN}=== Update complete! ===${NC}"
echo ""
echo "Backup location: $BACKUP_DIR"
echo "Current status:"
systemctl status "$SERVICE_NAME" --no-pager || true
echo ""
echo "Useful commands:"
echo "  View logs: sudo journalctl -u $SERVICE_NAME -f"
echo "  Status:    sudo systemctl status $SERVICE_NAME"
echo "  Restart:   sudo systemctl restart $SERVICE_NAME"
echo "  Restore:   sudo cp -r $BACKUP_DIR $INSTALL_DIR"
echo ""
echo -e "${YELLOW}You can safely delete the backup after verifying everything works:${NC}"
echo "  sudo rm -rf $BACKUP_DIR"
echo ""
