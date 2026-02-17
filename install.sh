#!/bin/bash
# Complete installation script for NoxFeed

set -e

# ===== CONFIGURATION =====
# UPDATE THIS with your repository URL
REPO_URL="https://github.com/YOUR_USERNAME/noxfeed.git"
# Optionally specify the branch (default: main)
REPO_BRANCH="main"
# =========================

# Variables
INSTALL_DIR="/home/nox/noxfeed"
SERVICE_NAME="noxfeed"
SERVICE_FILE="noxfeed.service"
SERVICE_USER="nox"
SERVICE_GROUP="nox"
TOKEN_FILE="/home/nox/.noxfeed_token"
VENV_DIR="$INSTALL_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== NoxFeed Installation Script ===${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

# Check for required commands
echo "Checking for required packages..."
MISSING_PACKAGES=()

if ! command -v git &> /dev/null; then
    MISSING_PACKAGES+=("git")
fi

if ! command -v python3 &> /dev/null; then
    MISSING_PACKAGES+=("python3")
fi

if ! python3 -m venv --help &> /dev/null 2>&1; then
    MISSING_PACKAGES+=("python3-venv")
fi

if ! command -v rtl_fm &> /dev/null; then
    MISSING_PACKAGES+=("rtl-sdr")
fi

if ! command -v multimon-ng &> /dev/null; then
    MISSING_PACKAGES+=("multimon-ng")
fi

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "${YELLOW}Missing packages: ${MISSING_PACKAGES[*]}${NC}"
    echo "Installing missing packages..."
    apt update
    apt install -y "${MISSING_PACKAGES[@]}"
fi

echo -e "${GREEN}All required packages are installed.${NC}"
echo ""

# Get GitHub token
GITHUB_TOKEN=""

if [ -f "$TOKEN_FILE" ]; then
    echo "Found existing GitHub token."
    read -p "Do you want to use the existing token? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        GITHUB_TOKEN=$(cat "$TOKEN_FILE")
        echo -e "${GREEN}Using saved token.${NC}"
    fi
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Please enter your GitHub Personal Access Token:"
    echo "(The token needs 'repo' permissions for private repositories)"
    read -s GITHUB_TOKEN
    echo ""
    
    if [ -z "$GITHUB_TOKEN" ]; then
        echo -e "${RED}No token provided. Exiting.${NC}"
        exit 1
    fi
    
    # Save token for future use
    echo "$GITHUB_TOKEN" > "$TOKEN_FILE"
    chmod 600 "$TOKEN_FILE"
    echo -e "${GREEN}Token saved to $TOKEN_FILE${NC}"
fi

# Create user and group if they don't exist
if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
    echo "Creating user: $SERVICE_USER"
    useradd --create-home --user-group --home-dir /home/nox --shell /bin/bash "$SERVICE_USER"
    echo -e "${GREEN}User $SERVICE_USER created.${NC}"
else
    echo "User $SERVICE_USER already exists."
fi

# Remove old installation if exists
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Installation directory already exists: $INSTALL_DIR${NC}"
    read -p "Do you want to remove it and reinstall? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing old installation..."
        rm -rf "$INSTALL_DIR"
    else
        echo -e "${RED}Installation cancelled.${NC}"
        exit 1
    fi
fi

# Clone repository
echo "Cloning repository from $REPO_URL (branch: $REPO_BRANCH)..."
CLONE_URL=$(echo "$REPO_URL" | sed "s|https://|https://${GITHUB_TOKEN}@|")

# Clone as nox user
sudo -u "$SERVICE_USER" git clone -b "$REPO_BRANCH" "$CLONE_URL" "$INSTALL_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to clone repository. Please check your token and repository URL.${NC}"
    exit 1
fi

echo -e "${GREEN}Repository cloned successfully.${NC}"

# Create necessary directories
echo "Creating directories..."
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/messages"
mkdir -p "$INSTALL_DIR/config"

# Create config from example if it doesn't exist
if [ ! -f "$INSTALL_DIR/config/config.json" ] && [ -f "$INSTALL_DIR/config/config.json.example" ]; then
    echo "Creating config.json from example..."
    cp "$INSTALL_DIR/config/config.json.example" "$INSTALL_DIR/config/config.json"
    echo -e "${YELLOW}Please edit $INSTALL_DIR/config/config.json with your settings!${NC}"
fi

# Create virtual environment
echo "Creating Python virtual environment..."
sudo -u "$SERVICE_USER" python3 -m venv "$VENV_DIR"

# Upgrade pip in venv
echo "Upgrading pip in virtual environment..."
sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install --upgrade pip

# Install requirements
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    echo "Installing Python dependencies..."
    sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
else
    echo -e "${YELLOW}Warning: requirements.txt not found. Skipping dependency installation.${NC}"
fi

# Set ownership
echo "Setting ownership to $SERVICE_USER:$SERVICE_GROUP"
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"

# Set ownership of token file
if [ -f "$TOKEN_FILE" ]; then
    chown "$SERVICE_USER:$SERVICE_GROUP" "$TOKEN_FILE"
fi

# Install systemd service
if [ -f "$INSTALL_DIR/$SERVICE_FILE" ]; then
    echo "Installing systemd service..."
    cp "$INSTALL_DIR/$SERVICE_FILE" "/etc/systemd/system/$SERVICE_FILE"
    
    # Reload systemd
    echo "Reloading systemd daemon..."
    systemctl daemon-reload
    
    # Enable service
    echo "Enabling $SERVICE_NAME service..."
    systemctl enable "$SERVICE_NAME"
else
    echo -e "${YELLOW}Warning: Service file not found at $INSTALL_DIR/$SERVICE_FILE${NC}"
fi

echo ""
echo -e "${GREEN}=== Installation complete! ===${NC}"
echo ""
echo "Installation directory: $INSTALL_DIR"
echo "Virtual environment: $VENV_DIR"
echo "Configuration file: $INSTALL_DIR/config/config.json"
echo "GitHub token saved: $TOKEN_FILE"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit configuration: sudo nano $INSTALL_DIR/config/config.json"
echo "   - Set your API token (api.token)"
echo "   - Set your Reverb app key (websocket.app_key)"
echo ""
echo "2. Start the service: sudo systemctl start $SERVICE_NAME"
echo "3. Check status: sudo systemctl status $SERVICE_NAME"
echo "4. View logs: sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Other useful commands:"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Update:  sudo ./update.sh (from the repository directory)"
echo ""
