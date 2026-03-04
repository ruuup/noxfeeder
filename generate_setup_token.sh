#!/bin/bash
# NoxFeed Setup Token Generator
# This script helps you create a setup token for NoxFeed installation

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     NoxFeed Setup Token Generator                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if base64 is available
if ! command -v base64 &> /dev/null; then
    echo -e "${YELLOW}Warning: base64 command not found${NC}"
    echo "Please install coreutils package"
    exit 1
fi

# Gather information
echo "Please enter the following information:"
echo ""

read -p "Feeder GUID: " FEEDER_GUID
echo ""

echo "WireGuard Configuration:"
read -p "  Private Key: " WG_PRIVATE_KEY
read -p "  Public Key:  " WG_PUBLIC_KEY
read -p "  IP Address:  " WG_IP
echo ""

# Validate inputs
if [ -z "$FEEDER_GUID" ] || [ -z "$WG_PRIVATE_KEY" ] || [ -z "$WG_PUBLIC_KEY" ] || [ -z "$WG_IP" ]; then
    echo -e "${YELLOW}Warning: Some fields are empty!${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# Create JSON (properly escaped)
SETUP_JSON=$(cat <<EOF
{
  "feeder_guid": "$FEEDER_GUID",
  "wireguard_private_key": "$WG_PRIVATE_KEY",
  "wireguard_public_key": "$WG_PUBLIC_KEY",
  "wireguard_ip": "$WG_IP"
}
EOF
)

# Base64 encode (remove newlines)
SETUP_TOKEN=$(echo "$SETUP_JSON" | base64 -w 0 2>/dev/null || echo "$SETUP_JSON" | base64)

# Display results
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Setup Token Generated Successfully                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Your setup token (copy this entire line):${NC}"
echo ""
echo "$SETUP_TOKEN"
echo ""
echo -e "${BLUE}How to use:${NC}"
echo "1. Copy the token above"
echo "2. Run the NoxFeed installation script on the target server:"
echo "   sudo ./install.sh --git"
echo "3. When asked 'Do you have a setup token?', answer 'y'"
echo "4. Paste the token when prompted"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Feeder GUID:  ${FEEDER_GUID:0:20}..."
echo "  WireGuard IP: $WG_IP"
echo ""
