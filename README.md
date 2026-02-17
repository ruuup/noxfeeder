# NoxFeeder

RTL-SDR POCSAG receiver with Laravel Reverb WebSocket integration.

## Features

- 📡 **POCSAG Reception**: Receives and decodes POCSAG512/1200/2400 messages
- 💾 **Local Storage**: Saves messages to daily JSON files
- 🌐 **API Integration**: Sends messages to Laravel backend
- 🔄 **Real-time Updates**: WebSocket connection for config updates and remote commands
- 📝 **Flexible Logging**: File, API, and console logging
- 🔧 **Remote Management**: Restart and update via API commands
- 🐍 **Virtual Environment**: Isolated Python environment

## Quick Start

### One-Line Installation (Easiest)

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/noxfeed/main/install.sh | sudo bash
```

Or if you prefer wget:
```bash
wget -qO- https://raw.githubusercontent.com/YOUR_USERNAME/noxfeed/main/install.sh | sudo bash
```

**Note:** Replace `YOUR_USERNAME` with your GitHub username before running.

### Automated Installation (Recommended)

For more control over the installation process:

1. Download and configure the installation script:
```bash
wget https://raw.githubusercontent.com/YOUR_USERNAME/noxfeed/main/install.sh
chmod +x install.sh

# Edit the script to set your repository URL
nano install.sh
# Update REPO_URL="https://github.com/YOUR_USERNAME/noxfeed.git"
```

2. Run the installation:
```bash
sudo ./install.sh
```

The script will:
- Check and install required system packages (git, python3, rtl-sdr, multimon-ng)
- Ask for your GitHub Personal Access Token (for private repo access)
- Save the token securely for future updates
- Clone the repository to `/home/nox/noxfeed`
- Create a Python virtual environment
- Install all dependencies
- Set up the systemd service
- Configure proper ownership and permissions

3. Configure the application:
```bash
sudo nano /home/nox/noxfeed/config/config.json
```
Set your API token and Reverb app key.

4. Start the service:
```bash
sudo systemctl start noxfeed
sudo journalctl -u noxfeed -f
```

### Updating

To update NoxFeed to the latest version:

```bash
cd /home/nox/noxfeed
sudo ./update.sh
```

The update script will:
- Stop the service
- Create a backup of the current installation
- Pull the latest changes from the repository
- Update Python dependencies
- Restore your configuration
- Restart the service
- Provide rollback instructions if something fails

### Uninstalling

To completely remove NoxFeed:

```bash
cd /home/nox/noxfeed
sudo ./uninstall.sh
```

The script will ask for confirmation and allow you to choose what to remove.

## GitHub Personal Access Token

For private repository access, you need a GitHub Personal Access Token:

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a descriptive name (e.g., "NoxFeed Server")
4. Set expiration (recommended: 90 days or No expiration for automation)
5. Select scopes:
   - ✅ `repo` (Full control of private repositories)
6. Click "Generate token"
7. **Copy the token immediately** (you won't see it again!)
8. Use this token when running `install.sh`

The token will be saved securely in `/home/nox/.noxfeed_token` for automatic updates.

**Security Note:** The token file is created with restricted permissions (600) and owned by the nox user.

## Installation Scripts Overview

### install.sh
Complete automated installation script:
- Checks and installs system dependencies
- Prompts for GitHub token (saved for future use)
- Clones the private repository
- Creates Python virtual environment
- Installs all dependencies
- Sets up systemd service
- Configures permissions

**Before running:** Edit `REPO_URL` in the script to match your repository.

### update.sh
Automated update script:
- Stops the service
- Creates timestamped backup
- Backs up configuration
- Pulls latest changes from repository
- Updates Python dependencies
- Restores configuration
- Restarts the service
- Provides rollback instructions on failure

Safe to run multiple times.

### uninstall.sh
Clean removal script:
- Stops and disables the service
- Removes systemd service file
- Optionally removes installation directory
- Optionally removes user account
- Optionally removes saved token

Interactive prompts for each removal step.

### install_service.sh (legacy)
Original service installation script. Use `install.sh` instead for new installations.

## Manual Installation

### Requirements
- Python 3.7+
- python3-venv
- rtl-sdr
- multimon-ng

### Installation as systemd service

The service runs in a Python virtual environment for isolation and is designed for Debian-based systems.

1. Install system requirements:
```bash
# Debian/Ubuntu
sudo apt update
sudo apt install python3 python3-venv python3-pip rtl-sdr multimon-ng
```

2. Clone or copy the project to the target directory:
```bash
# As the nox user (or copy files as root and adjust ownership)
mkdir -p /home/nox/noxfeed
cd /home/nox/noxfeed
# Copy all project files here
```

3. Create and edit your configuration:
```bash
cp config/config.json.example config/config.json
nano config/config.json  # Edit with your settings
```

4. Run the installation script:
```bash
sudo chmod +x install_service.sh
sudo ./install_service.sh
```

The installation script will:
- Create the `nox` user and group (if not exists)
- Install to `/home/nox/noxfeed`
- Create a Python virtual environment at `/home/nox/noxfeed/venv`
- Install all Python dependencies
- Set up the systemd service

5. Configure your API token and Reverb app key in `/home/nox/noxfeed/config/config.json`

6. Start the service:
```bash
sudo systemctl start noxfeed
```

### Manual Installation (with venv)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python3 noxfeed.py
```

### Development Setup

For quick setup, use the provided scripts:

**Linux/macOS:**
```bash
chmod +x setup_venv.sh
./setup_venv.sh
source venv/bin/activate
```

**Windows:**
```cmd
setup_venv.bat
venv\Scripts\activate
```

**Manual setup:**
```bash
# Create and activate venv
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run with custom logging
python3 noxfeed.py -l console
```

## Command Line Arguments

```bash
python3 noxfeed.py -l [targets...]
```

**Logging targets:**
- `file` - Log to file (logs/noxfeed.log)
- `api` - Log API interactions
- `console` - Log to console (stdout)

**Default:** `file api`

**Examples:**
```bash
# Default (file + api logging)
python3 noxfeed.py

# Console logging only
python3 noxfeed.py -l console

# All logging targets
python3 noxfeed.py -l file api console

# File logging only
python3 noxfeed.py -l file
```

## WebSocket Configuration (Laravel Reverb)

The application connects to Laravel Reverb using the Pusher protocol. Configure in `config/config.json`:

```json
"websocket": {
    "host": "nox.lwyrup.at",
    "port": 443,
    "secure": true,
    "app_key": "your-reverb-app-key",
    "channel": "config-updates",
    "event": "config.updated",
    "token": "",
    "reconnect_delay": 5
}
```

**Parameters:**
- `host`: Reverb server domain (nox.lwyrup.at)
- `port`: WebSocket port (443 for secure connections)
- `secure`: Use WSS (true) or WS (false)
- `app_key`: Laravel Reverb application key
- `channel`: Channel to subscribe to
- `event`: Event name to listen for
- `token`: Optional Bearer token for authentication
- `reconnect_delay`: Seconds to wait before reconnecting

The WebSocket listener will automatically:
1. Connect to the Reverb server
2. Subscribe to the specified channel
3. Listen for events
4. Trigger config updates when events are received

## systemd Service Management

```bash
# Start service
sudo systemctl start noxfeed

# Stop service
sudo systemctl stop noxfeed

# Restart service
sudo systemctl restart noxfeed

# Check status
sudo systemctl status noxfeed

# View logs
sudo journalctl -u noxfeed -f

# Enable auto-start on boot
sudo systemctl enable noxfeed

# Disable auto-start on boot
sudo systemctl disable noxfeed
```

## Configuration

Configuration file: `/home/nox/noxfeed/config/config.json` (when installed as service) or `config/config.json` (manual installation).

**Important:** Copy `config/config.json.example` to `config/config.json` and adjust the values:
```bash
cp config/config.json.example config/config.json
```

**Required settings:**
- `api.token` - Your Laravel API authentication token
- `websocket.app_key` - Your Laravel Reverb application key

### RTL-FM Configuration

The RTL-SDR receiver is configured for POCSAG reception:

```json
"rtl_fm": {
  "command": "rtl_fm",
  "args": [
    "-f", "168.075M",    // Frequency
    "-p", "30",          // PPM correction
    "-g", "100",         // Gain
    "-s", "22050",       // Sample rate
    "-l", "1"            // Squelch level
  ]
}
```

### Message Storage

Received POCSAG messages are stored in `/home/nox/noxfeed/messages/` organized by date:

```json
[
  {
    "protocol": "POCSAG1200",
    "address": "1234567",
    "function": "3",
    "type": "alpha",
    "message": "Message text",
    "timestamp": "2026-02-15T10:30:45.123456",
    "raw": "Original line from multimon-ng"
  }
]
```

Messages are also sent to Laravel API endpoint `/messages`.

## API Configuration

```json
"api": {
    "base_url": "https://nox.lwyrup.at/api",
    "token": "your-api-token",
    "config_endpoint": "/config",
    "messages_endpoint": "/messages",
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 5
}
```

## Remote Commands

The service can be controlled remotely via WebSocket commands from the Laravel backend:

### Restart Service
```php
use App\Events\CommandEvent;

broadcast(new CommandEvent([
    'command' => 'restart',
    'params' => []
]));
```

### Update from Git
```php
broadcast(new CommandEvent([
    'command' => 'update',
    'params' => []
]));
```

### Reload Configuration
```php
use App\Events\ConfigUpdatedEvent;

broadcast(new ConfigUpdatedEvent($newConfig));
```

## WebSocket Channels

The service subscribes to two channels:

1. **config-updates**: Receives configuration change notifications
2. **commands**: Receives remote commands (restart, update)

## Project Structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed project structure and component documentation.

## API Endpoints

The service communicates with these Laravel API endpoints:

- `GET /config` - Fetch current configuration
- `POST /messages` - Send received POCSAG messages

## Development

For local development and testing:

```bash
cd /home/nox/noxfeed
source venv/bin/activate

# Run with console logging
python3 noxfeed.py -l console

# Run with all logging
python3 noxfeed.py -l file api console
```


