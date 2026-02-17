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

## Installation

The project includes a **universal installation script** that handles all installation scenarios.

### Installation Modes

#### 1. Production (Git Clone) - Default

Recommended for production deployment. Clones from Git repository and sets up systemd service.

```bash
# Download the installation script
wget https://raw.githubusercontent.com/Ruuup/noxfeed/main/install.sh
chmod +x install.sh

# Edit REPO_URL if needed
nano install.sh

# Run installation
sudo ./install.sh --git
```

**What it does:**
- Installs system packages (git, python3, rtl-sdr, multimon-ng)
- Asks for GitHub Personal Access Token (saved for updates)
- Clones repository to `/home/nox/noxfeed`
- Creates Python virtual environment
- Installs Python dependencies
- Sets up systemd service
- Configures proper permissions

#### 2. Local Installation

Install from a local copy without Git clone. Useful if you've already downloaded the files.

```bash
cd /path/to/noxfeed-source
sudo ./install.sh --local
```

**What it does:**
- Copies files from current directory to `/home/nox/noxfeed`
- Creates Python virtual environment
- Installs dependencies
- Sets up systemd service

#### 3. Development Mode

For local development and testing. No root required, no systemd service.

```bash
cd /path/to/noxfeed-source
./install.sh --dev
```

**What it does:**
- Creates virtual environment in current directory
- Installs dependencies
- Ready for development/testing
- No systemd service installation

### Installation Options

```bash
Usage: ./install.sh [OPTIONS]

Installation Modes:
  --git              Clone from Git repository (default if run as root)
  --local            Install from current directory
  --dev              Development setup (no systemd, no root required)

Options:
  --install-dir DIR  Custom installation directory (default: /home/nox/noxfeed)
  --user USER        Service user (default: nox)
  --skip-service     Don't install systemd service
  --no-token         Skip GitHub token (for public repos)
  --help             Show help message

Examples:
  # Standard production installation
  sudo ./install.sh --git

  # Custom installation directory
  sudo ./install.sh --git --install-dir /opt/noxfeed

  # Install without systemd service
  sudo ./install.sh --local --skip-service

  # Development setup
  ./install.sh --dev
```

### One-Line Installation

For quick remote installations:

```bash
curl -sSL https://raw.githubusercontent.com/Ruuup/noxfeed/main/install.sh | sudo bash
```

Or with wget:
```bash
wget -qO- https://raw.githubusercontent.com/Ruuup/noxfeed/main/install.sh | sudo bash
```

### Post-Installation

1. **Configure the application:**
```bash
sudo nano /home/nox/noxfeed/config/config.json
```

Set your API token and Reverb app key:
```json
{
  "api": {
    "token": "your-api-token-here"
  },
  "websocket": {
    "app_key": "your-reverb-app-key-here"
  }
}
```

2. **Start the service:**
```bash
sudo systemctl start noxfeed
```

3. **Check status:**
```bash
sudo systemctl status noxfeed
sudo journalctl -u noxfeed -f
```

## Updating

To update NoxFeed to the latest version:

```bash
cd /home/nox/noxfeed
sudo ./update.sh
```

The update script will:
- Stop the service
- Create a timestamped backup
- Pull latest changes from Git
- Update Python dependencies
- Restore your configuration
- Restart the service
- Provide rollback instructions if something fails

**Options:**
```bash
sudo ./update.sh [OPTIONS]

Options:
  --install-dir DIR   Installation directory (default: /home/nox/noxfeed)
  --user USER         Service user (default: nox)
  --service NAME      Service name (default: noxfeed)
  --branch BRANCH     Git branch to pull (default: main)
  --help, -h          Show help message
```

**Examples:**
```bash
# Standard update
sudo ./update.sh

# Update from different branch
sudo ./update.sh --branch develop

# Update custom installation
sudo ./update.sh --install-dir /opt/myapp --user myuser
```

## Uninstalling

To completely remove NoxFeed:

```bash
cd /home/nox/noxfeed
sudo ./uninstall.sh
```

Interactive prompts allow you to choose what to remove (service, files, user, token).

**Options:**
```bash
sudo ./uninstall.sh [OPTIONS]

Options:
  --install-dir DIR   Installation directory (default: /home/nox/noxfeed)
  --user USER         Service user (default: nox)
  --service NAME      Service name (default: noxfeed)
  --help, -h          Show help message
```

**Examples:**
```bash
# Standard uninstall
sudo ./uninstall.sh

# Uninstall custom installation
sudo ./uninstall.sh --install-dir /opt/myapp --user myuser --service myservice
```

**Note:** System packages (python3, rtl-sdr, multimon-ng, git) are NOT removed automatically as they may be used by other applications.

## GitHub Personal Access Token

For **private repository** access, you need a GitHub Personal Access Token:

1. Go to: GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name (e.g., "NoxFeed Server")
4. Set expiration (90 days or No expiration)
5. Select scope: ✅ `repo` (Full control of private repositories)
6. Generate and **copy the token immediately**
7. Paste when prompted during installation

The token is saved in `/home/nox/.noxfeed_token` (permissions: 600) for automatic updates.

**For public repositories:** Use `--no-token` flag to skip token prompt.

## Manual Installation

If you prefer manual setup or need custom control:

### Requirements
- Python 3.7+
- python3-venv
- rtl-sdr
- multimon-ng

### Steps

1. **Install system packages:**
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip rtl-sdr multimon-ng
```

2. **Create installation directory:**
```bash
sudo mkdir -p /home/nox/noxfeed
cd /home/nox/noxfeed
# Copy or clone project files here
```

3. **Configure:**
```bash
cp config/config.json.example config/config.json
sudo nano config/config.json
```

4. **Use the installation script:**
```bash
sudo ./install.sh --local
```

Or follow the script manually if needed.

## Development Setup

For local development without systemd:

```bash
cd /path/to/noxfeed
./install.sh --dev

# Activate venv
source venv/bin/activate

# Run with console logging
python3 noxfeed.py -l console

# Deactivate when done
deactivate
```
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

Use the unified installation script in development mode:

```bash
# Development mode (creates venv in current directory)
sudo bash install.sh --dev

# Activate the virtual environment
source venv/bin/activate

# Run with custom logging
python3 noxfeed.py -l console
```

**Manual setup without install script:**
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

The application connects to Laravel Reverb using the Pusher protocol and subscribes to two channels. Configure in `config/config.json`:

```json
"websocket": {
    "host": "nox.lwyrup.at",
    "port": 443,
    "secure": true,
    "app_key": "your-reverb-app-key",
    "channels": {
        "config": "config-updates",
        "commands": "commands"
    },
    "events": {
        "config": "config.updated",
        "commands": "command.execute"
    },
    "token": "",
    "reconnect_delay": 5
}
```

**Parameters:**
- `host`: Reverb server domain (nox.lwyrup.at)
- `port`: WebSocket port (443 for secure connections)
- `secure`: Use WSS (true) or WS (false)
- `app_key`: Laravel Reverb application key
- `channels.config`: Channel name for configuration updates
- `channels.commands`: Channel name for remote commands
- `events.config`: Event name for configuration changes
- `events.commands`: Event name for command execution
- `token`: Optional Bearer token for authentication
- `reconnect_delay`: Seconds to wait before reconnecting

The WebSocket listener will automatically:
1. Connect to the Reverb server
2. Subscribe to both channels (config-updates and commands)
3. Listen for events on both channels
4. Trigger config updates or execute commands when events are received

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


