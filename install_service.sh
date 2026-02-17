#!/bin/bash
# Installation script for NoxFeed systemd service

set -e

# Variables
SERVICE_NAME="noxfeed"
SERVICE_FILE="noxfeed.service"
INSTALL_DIR="/home/nox/noxfeed"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_USER="nox"
SERVICE_GROUP="nox"

echo "Installing NoxFeed systemd service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Check for python3 and python3-venv
echo "Checking for Python 3 and venv..."
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install python3 first."
    exit 1
fi

if ! python3 -m venv --help &> /dev/null; then
    echo "Error: python3-venv is not installed."
    echo "Please install it with: sudo apt install python3-venv"
    exit 1
fi

# Create user and group if they don't exist
if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
    echo "Creating user: $SERVICE_USER"
    useradd --create-home --user-group --home-dir /home/nox --shell /bin/bash "$SERVICE_USER"
fi

# Create installation directory
echo "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/messages"
mkdir -p "$INSTALL_DIR/config"

# Copy files
echo "Copying application files..."
cp -r ./* "$INSTALL_DIR/"

# Create config from example if it doesn't exist
if [ ! -f "$INSTALL_DIR/config/config.json" ] && [ -f "$INSTALL_DIR/config/config.json.example" ]; then
    echo "Creating config.json from example..."
    cp "$INSTALL_DIR/config/config.json.example" "$INSTALL_DIR/config/config.json"
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv "$VENV_DIR"

# Upgrade pip in venv
echo "Upgrading pip in virtual environment..."
"$VENV_DIR/bin/pip" install --upgrade pip

# Install requirements
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    echo "Installing Python dependencies..."
    "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
else
    echo "Warning: requirements.txt not found. Skipping dependency installation."
fi

# Set ownership
echo "Setting ownership to $SERVICE_USER:$SERVICE_GROUP"
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"

# Install systemd service
echo "Installing systemd service..."
cp "$INSTALL_DIR/$SERVICE_FILE" "/etc/systemd/system/$SERVICE_FILE"

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable service
echo "Enabling $SERVICE_NAME service..."
systemctl enable "$SERVICE_NAME"

echo ""
echo "Installation complete!"
echo ""
echo "Virtual environment created at: $VENV_DIR"
echo "To configure the service, edit: $INSTALL_DIR/config/config.json"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "To manually activate the venv:"
echo "  source $VENV_DIR/bin/activate"
echo ""
