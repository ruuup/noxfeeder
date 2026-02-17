#!/bin/bash
# NoxFeed Universal Installation Script
# Supports: Git clone, local installation, development setup, and systemd service

set -e

# ===== CONFIGURATION =====
REPO_URL="https://github.com/Ruuup/noxfeed.git"
REPO_BRANCH="main"
# =========================

# Default values
INSTALL_DIR="/home/nox/noxfeed"
SERVICE_NAME="noxfeed"
SERVICE_FILE="noxfeed.service"
SERVICE_USER="nox"
SERVICE_GROUP="nox"
TOKEN_FILE="/home/nox/.noxfeed_token"
VENV_DIR=""
INSTALL_MODE=""
SKIP_SERVICE=false
IS_DEV_MODE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===== FUNCTIONS =====

show_help() {
    cat << EOF
NoxFeed Installation Script

Usage: sudo ./install.sh [OPTIONS]

Installation Modes:
  --git              Clone from Git repository (default if run as root)
  --local            Install from current directory
  --dev              Development setup (local venv only, no systemd)

Options:
  --install-dir DIR  Installation directory (default: /home/nox/noxfeed)
  --user USER        Service user (default: nox)
  --skip-service     Don't install systemd service
  --no-token         Skip GitHub token (public repo or already cloned)
  --help             Show this help message

Examples:
  # Full installation with Git clone (production)
  sudo ./install.sh --git

  # Install from current directory
  sudo ./install.sh --local

  # Development setup (no root required)
  ./install.sh --dev

  # Custom installation directory
  sudo ./install.sh --git --install-dir /opt/myapp

EOF
    exit 0
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This installation mode requires root privileges"
        echo "Please run with: sudo $0 $*"
        exit 1
    fi
}

check_system_packages() {
    log_step "Checking for required system packages..."
    
    local MISSING_PACKAGES=()
    
    if [ "$INSTALL_MODE" = "git" ] && ! command -v git &> /dev/null; then
        MISSING_PACKAGES+=("git")
    fi
    
    if ! command -v python3 &> /dev/null; then
        MISSING_PACKAGES+=("python3")
    fi
    
    if ! python3 -m venv --help &> /dev/null 2>&1; then
        MISSING_PACKAGES+=("python3-venv")
    fi
    
    if [ "$IS_DEV_MODE" = false ]; then
        if ! command -v rtl_fm &> /dev/null; then
            MISSING_PACKAGES+=("rtl-sdr")
        fi
        
        if ! command -v multimon-ng &> /dev/null; then
            MISSING_PACKAGES+=("multimon-ng")
        fi
    fi
    
    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        log_warn "Missing packages: ${MISSING_PACKAGES[*]}"
        
        if [ "$EUID" -eq 0 ]; then
            echo "Installing missing packages..."
            apt update
            apt install -y "${MISSING_PACKAGES[@]}"
            log_info "Packages installed successfully"
        else
            log_error "Please install missing packages manually:"
            echo "  sudo apt install ${MISSING_PACKAGES[*]}"
            exit 1
        fi
    else
        log_info "All required packages are installed"
    fi
}

get_github_token() {
    local GITHUB_TOKEN=""
    
    if [ -f "$TOKEN_FILE" ]; then
        log_info "Found existing GitHub token"
        read -p "Do you want to use the existing token? (Y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            GITHUB_TOKEN=$(cat "$TOKEN_FILE")
            log_info "Using saved token"
            echo "$GITHUB_TOKEN"
            return 0
        fi
    fi
    
    echo ""
    echo "Please enter your GitHub Personal Access Token:"
    echo "(Press Enter to skip if using public repository)"
    echo "(Token needs 'repo' permissions for private repositories)"
    read -s GITHUB_TOKEN
    echo ""
    
    if [ -n "$GITHUB_TOKEN" ]; then
        echo "$GITHUB_TOKEN" > "$TOKEN_FILE"
        chmod 600 "$TOKEN_FILE"
        log_info "Token saved to $TOKEN_FILE"
    fi
    
    echo "$GITHUB_TOKEN"
}

create_service_user() {
    if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
        log_step "Creating user: $SERVICE_USER"
        useradd --create-home --user-group --home-dir "/home/$SERVICE_USER" --shell /bin/bash "$SERVICE_USER"
        log_info "User $SERVICE_USER created"
    else
        log_info "User $SERVICE_USER already exists"
    fi
}

clone_repository() {
    log_step "Cloning repository from $REPO_URL (branch: $REPO_BRANCH)..."
    
    local GITHUB_TOKEN=$(get_github_token)
    local CLONE_URL="$REPO_URL"
    
    if [ -n "$GITHUB_TOKEN" ]; then
        CLONE_URL=$(echo "$REPO_URL" | sed "s|https://|https://${GITHUB_TOKEN}@|")
    fi
    
    # Remove old installation if exists
    if [ -d "$INSTALL_DIR" ]; then
        log_warn "Installation directory already exists: $INSTALL_DIR"
        read -p "Do you want to remove it and reinstall? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_step "Removing old installation..."
            rm -rf "$INSTALL_DIR"
        else
            log_error "Installation cancelled"
            exit 1
        fi
    fi
    
    # Clone as service user
    sudo -u "$SERVICE_USER" git clone -b "$REPO_BRANCH" "$CLONE_URL" "$INSTALL_DIR"
    
    if [ $? -ne 0 ]; then
        log_error "Failed to clone repository"
        echo "Please check your token and repository URL"
        exit 1
    fi
    
    log_info "Repository cloned successfully"
}

copy_local_files() {
    log_step "Installing from current directory..."
    
    # Create installation directory if it doesn't exist
    mkdir -p "$INSTALL_DIR"
    
    # Copy all files except venv and other temporary directories
    log_step "Copying application files..."
    rsync -av --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
          --exclude='.git' --exclude='messages' --exclude='logs' \
          ./ "$INSTALL_DIR/" 2>/dev/null || cp -r ./* "$INSTALL_DIR/" 2>/dev/null || true
    
    log_info "Files copied successfully"
}

setup_directories() {
    log_step "Creating necessary directories..."
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$INSTALL_DIR/messages"
    mkdir -p "$INSTALL_DIR/config"
    log_info "Directories created"
}

setup_config() {
    if [ ! -f "$INSTALL_DIR/config/config.json" ] && [ -f "$INSTALL_DIR/config/config.json.example" ]; then
        log_step "Creating config.json from example..."
        cp "$INSTALL_DIR/config/config.json.example" "$INSTALL_DIR/config/config.json"
        log_warn "Please edit $INSTALL_DIR/config/config.json with your settings!"
    fi
}

setup_venv() {
    log_step "Creating Python virtual environment at $VENV_DIR..."
    
    # Check if venv already exists
    if [ -d "$VENV_DIR" ]; then
        log_warn "Virtual environment already exists at $VENV_DIR"
        
        if [ "$IS_DEV_MODE" = true ]; then
            read -p "Do you want to recreate it? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log_step "Removing existing virtual environment..."
                rm -rf "$VENV_DIR"
            else
                log_info "Using existing virtual environment"
                return 0
            fi
        fi
    fi
    
    # Create venv
    if [ "$IS_DEV_MODE" = true ]; then
        python3 -m venv "$VENV_DIR"
    else
        sudo -u "$SERVICE_USER" python3 -m venv "$VENV_DIR"
    fi
    
    log_info "Virtual environment created"
    
    # Upgrade pip
    log_step "Upgrading pip..."
    if [ "$IS_DEV_MODE" = true ]; then
        "$VENV_DIR/bin/pip" install --upgrade pip -q
    else
        sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install --upgrade pip -q
    fi
    
    # Install requirements
    if [ -f "$INSTALL_DIR/requirements.txt" ]; then
        log_step "Installing Python dependencies..."
        if [ "$IS_DEV_MODE" = true ]; then
            "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q
        else
            sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q
        fi
        log_info "Dependencies installed"
    else
        log_warn "requirements.txt not found, skipping dependency installation"
    fi
}

set_permissions() {
    log_step "Setting ownership to $SERVICE_USER:$SERVICE_GROUP..."
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
    
    if [ -f "$TOKEN_FILE" ]; then
        chown "$SERVICE_USER:$SERVICE_GROUP" "$TOKEN_FILE"
    fi
    
    log_info "Permissions set"
}

install_systemd_service() {
    if [ -f "$INSTALL_DIR/$SERVICE_FILE" ]; then
        log_step "Installing systemd service..."
        cp "$INSTALL_DIR/$SERVICE_FILE" "/etc/systemd/system/$SERVICE_FILE"
        
        systemctl daemon-reload
        systemctl enable "$SERVICE_NAME"
        
        log_info "systemd service installed and enabled"
    else
        log_warn "Service file not found at $INSTALL_DIR/$SERVICE_FILE"
    fi
}

show_completion_message() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Installation Complete!                         ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if [ "$IS_DEV_MODE" = true ]; then
        echo -e "${BLUE}Development Setup:${NC}"
        echo "  Installation directory: $INSTALL_DIR"
        echo "  Virtual environment: $VENV_DIR"
        echo ""
        echo -e "${YELLOW}To activate the virtual environment:${NC}"
        echo "  cd $INSTALL_DIR"
        echo "  source $VENV_DIR/bin/activate"
        echo ""
        echo -e "${YELLOW}To run the application:${NC}"
        echo "  python3 noxfeed.py -l console"
        echo ""
        echo -e "${YELLOW}To deactivate:${NC}"
        echo "  deactivate"
    else
        echo -e "${BLUE}Installation Summary:${NC}"
        echo "  Installation directory: $INSTALL_DIR"
        echo "  Virtual environment: $VENV_DIR"
        echo "  Configuration file: $INSTALL_DIR/config/config.json"
        if [ -f "$TOKEN_FILE" ]; then
            echo "  GitHub token saved: $TOKEN_FILE"
        fi
        echo ""
        echo -e "${YELLOW}Next steps:${NC}"
        echo "1. Edit configuration:"
        echo "   sudo nano $INSTALL_DIR/config/config.json"
        echo "   - Set your API token (api.token)"
        echo "   - Set your Reverb app key (websocket.app_key)"
        echo ""
        
        if [ "$SKIP_SERVICE" = false ]; then
            echo "2. Start the service:"
            echo "   sudo systemctl start $SERVICE_NAME"
            echo ""
            echo "3. Check status:"
            echo "   sudo systemctl status $SERVICE_NAME"
            echo ""
            echo "4. View logs:"
            echo "   sudo journalctl -u $SERVICE_NAME -f"
            echo ""
            echo -e "${BLUE}Other useful commands:${NC}"
            echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
            echo "  Restart: sudo systemctl restart $SERVICE_NAME"
            echo "  Update:  cd $INSTALL_DIR && sudo ./update.sh"
        else
            echo "2. Run manually:"
            echo "   cd $INSTALL_DIR"
            echo "   sudo -u $SERVICE_USER $VENV_DIR/bin/python noxfeed.py"
        fi
    fi
    
    echo ""
}

# ===== MAIN SCRIPT =====

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --git)
            INSTALL_MODE="git"
            shift
            ;;
        --local)
            INSTALL_MODE="local"
            shift
            ;;
        --dev)
            INSTALL_MODE="dev"
            IS_DEV_MODE=true
            shift
            ;;
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --user)
            SERVICE_USER="$2"
            SERVICE_GROUP="$2"
            shift 2
            ;;
        --skip-service)
            SKIP_SERVICE=true
            shift
            ;;
        --no-token)
            TOKEN_FILE=""
            shift
            ;;
        --help|-h)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Determine installation mode if not specified
if [ -z "$INSTALL_MODE" ]; then
    if [ "$EUID" -eq 0 ]; then
        # Running as root - default to git mode
        INSTALL_MODE="git"
        log_info "No mode specified, defaulting to --git"
    else
        # Not running as root - default to dev mode
        INSTALL_MODE="dev"
        IS_DEV_MODE=true
        log_info "Running as non-root user, defaulting to --dev mode"
    fi
fi

# Set venv directory based on mode
if [ "$IS_DEV_MODE" = true ]; then
    VENV_DIR="$INSTALL_DIR/venv"
    if [ "$INSTALL_DIR" = "/home/nox/noxfeed" ]; then
        INSTALL_DIR="$(pwd)"
    fi
    VENV_DIR="$INSTALL_DIR/venv"
else
    VENV_DIR="$INSTALL_DIR/venv"
fi

# Display banner
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          NoxFeed Installation Script                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Mode:${NC} $INSTALL_MODE"
echo -e "${BLUE}Installation Directory:${NC} $INSTALL_DIR"
echo -e "${BLUE}Virtual Environment:${NC} $VENV_DIR"
if [ "$IS_DEV_MODE" = false ]; then
    echo -e "${BLUE}Service User:${NC} $SERVICE_USER"
fi
echo ""

# Check root privileges if needed
if [ "$IS_DEV_MODE" = false ]; then
    check_root
fi

# Check system packages
check_system_packages

# Create service user (production only)
if [ "$IS_DEV_MODE" = false ]; then
    create_service_user
fi

# Install based on mode
case $INSTALL_MODE in
    git)
        clone_repository
        ;;
    local)
        copy_local_files
        ;;
    dev)
        log_info "Development mode - using current directory"
        ;;
esac

# Setup directories
setup_directories

# Setup configuration
setup_config

# Setup virtual environment
setup_venv

# Set permissions (production only)
if [ "$IS_DEV_MODE" = false ]; then
    set_permissions
fi

# Install systemd service (production only, unless skipped)
if [ "$IS_DEV_MODE" = false ] && [ "$SKIP_SERVICE" = false ]; then
    install_systemd_service
fi

# Show completion message
show_completion_message

exit 0
