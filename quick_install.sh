#!/bin/bash
# Quick installation one-liner for NoxFeed
# Usage: curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/noxfeed/main/quick_install.sh | sudo bash

# ===== CONFIGURATION =====
REPO_URL="https://github.com/YOUR_USERNAME/noxfeed.git"
REPO_BRANCH="main"
INSTALL_SCRIPT_URL="https://raw.githubusercontent.com/YOUR_USERNAME/noxfeed/$REPO_BRANCH/install.sh"
# =========================

set -e

echo "=== NoxFeed Quick Install ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use: sudo bash)"
    exit 1
fi

# Download and run installation script
echo "Downloading installation script..."
TMP_INSTALL="/tmp/noxfeed_install_$$.sh"

if command -v curl &> /dev/null; then
    curl -sSL "$INSTALL_SCRIPT_URL" -o "$TMP_INSTALL"
elif command -v wget &> /dev/null; then
    wget -q "$INSTALL_SCRIPT_URL" -O "$TMP_INSTALL"
else
    echo "Error: Neither curl nor wget is installed."
    echo "Please install curl: sudo apt install curl"
    exit 1
fi

# Make executable and run
chmod +x "$TMP_INSTALL"

# Update the REPO_URL in the downloaded script
sed -i "s|REPO_URL=.*|REPO_URL=\"$REPO_URL\"|" "$TMP_INSTALL"
sed -i "s|REPO_BRANCH=.*|REPO_BRANCH=\"$REPO_BRANCH\"|" "$TMP_INSTALL"

# Run installation
"$TMP_INSTALL"

# Cleanup
rm "$TMP_INSTALL"

echo ""
echo "Quick install complete!"
