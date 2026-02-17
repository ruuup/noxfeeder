# NoxFeed - Projekt-Struktur

## Übersicht

NoxFeed ist ein RTL-SDR POCSAG Empfänger mit Laravel-Backend-Integration.

## Verzeichnisstruktur

```
/home/nox/noxfeed/
├── noxfeed.py                 # Hauptscript
├── requirements.txt           # Python-Abhängigkeiten
├── noxfeed.service           # systemd Service-Datei
├── install.sh                # Installations-Script
├── update.sh                 # Update-Script
├── uninstall.sh              # Deinstallations-Script
├── setup_venv.sh             # Lokales Setup (Development)
│
├── config/
│   ├── config.json           # Aktuelle Konfiguration (gitignored)
│   └── config.json.example   # Konfigurations-Vorlage
│
├── logs/                     # Log-Dateien (gitignored)
│   └── noxfeed.log
│
├── messages/                 # Empfangene POCSAG-Nachrichten (gitignored)
│   ├── 20260215.json
│   └── ...
│
├── venv/                     # Python Virtual Environment (gitignored)
│
└── includes/
    ├── api/                  # API-Client für Laravel
    │   ├── __init__.py
    │   ├── laravel_api_client.py
    │   ├── configuration_api.py
    │   ├── data_api.py
    │   └── logging_api.py
    │
    ├── config/               # Konfigurations-Management
    │   ├── __init__.py
    │   └── config.py
    │
    ├── logger/               # Logging-System
    │   ├── __init__.py
    │   └── logger.py
    │
    ├── realtime/             # WebSocket-Client (Laravel Reverb)
    │   ├── __init__.py
    │   └── laravel_websocket_listener.py
    │
    ├── worker/               # RTL-SDR Worker
    │   ├── __init__.py
    │   ├── rtl_fm_worker.py
    │   └── multimon_worker.py
    │
    └── handlers/             # Message & Command Handler
        ├── __init__.py
        ├── message_handler.py
        └── command_handler.py
```

## Komponenten

### Hauptscript (noxfeed.py)
- Startet rtl_fm Prozess
- Startet multimon-ng Prozess
- Verarbeitet empfangene POCSAG-Nachrichten
- Kommuniziert mit Laravel API
- Hört auf WebSocket-Events

### Worker

#### rtl_fm_worker.py
- Startet und verwaltet den rtl_fm Prozess
- Konfigurierbare Parameter über config.json
- Aktuelle Einstellungen: 168.075 MHz, gain 100

#### multimon_worker.py
- Startet und verwaltet multimon-ng Prozess
- Dekodiert POCSAG512, POCSAG1200, POCSAG2400
- Streamt Output für Verarbeitung

### Handler

#### message_handler.py
**Funktionen:**
- Parst POCSAG-Nachrichten von multimon-ng Output
- Speichert Nachrichten lokal in JSON-Dateien (organisiert nach Datum)
- Sendet Nachrichten an Laravel API
- Logging aller Aktivitäten

**Nachrichtenformat:**
```json
{
  "protocol": "POCSAG1200",
  "address": "1234567",
  "function": "3",
  "type": "alpha",
  "message": "Nachrichtentext",
  "timestamp": "2026-02-15T10:30:45.123456",
  "raw": "Originale Zeile von multimon-ng"
}
```

#### command_handler.py
**Unterstützte Befehle:**
- `restart` - Neustart des Services via systemd
- `update` - Pull von Git und Neustart
- `reload_config` - Konfiguration neu laden

### API-Client (laravel_api_client.py)
- HTTP-Client für Laravel-Backend
- Automatische Token-Authentifizierung
- Retry-Logik bei Fehlern
- Endpoints:
  - `/config` - Konfiguration laden/speichern
  - `/messages` - POCSAG-Nachrichten senden

### WebSocket-Listener (laravel_websocket_listener.py)
- Implementiert Pusher/Reverb-Protokoll
- Zwei Channels:
  - `config-updates` - Konfigurationsänderungen
  - `commands` - Remote-Befehle (restart, update)
- Automatische Reconnects
- Event-Handler für verschiedene Message-Types

### Logging-System (logger.py)
**Drei Logger:**
1. **file_logger** - Schreibt in logs/noxfeed.log
2. **api_logger** - Für API-bezogene Logs
3. **console_logger** - Für Console-Output

**Konfigurierbar via `-l` Parameter:**
```bash
python3 noxfeed.py -l file api        # Standard (systemd)
python3 noxfeed.py -l console         # Nur Console
python3 noxfeed.py -l file api console # Alle
```

### Konfigurations-Management (config.py)
- Lädt config.json beim Start
- Unterstützt Dot-Notation: `config.get("api.base_url")`
- Kann von API aktualisiert werden
- Optional: Persistenz aktivierbar

## Datenfluss

### POCSAG-Empfang
```
rtl_fm (168.075 MHz)
    ↓ (raw audio)
multimon-ng (POCSAG Decoder)
    ↓ (decoded text)
message_handler
    ├─→ Lokale Speicherung (messages/YYYYMMDD.json)
    └─→ Laravel API (/messages)
```

### Konfiguration
```
Laravel Backend
    ↓ (WebSocket: config.updated Event)
LaravelWebSocketListener
    ↓
handle_config_update()
    ├─→ API-Aufruf (/config)
    └─→ config.update_from_dict()
```

### Remote-Befehle
```
Laravel Backend
    ↓ (WebSocket: command.execute Event)
LaravelWebSocketListener
    ↓
handle_command()
    ↓
CommandHandler
    ├─→ restart → systemctl restart noxfeed
    ├─→ update → ./update.sh
    └─→ reload_config → Handled by config system
```

## Konfiguration

### RTL-FM Parameter (config.json)
```json
"rtl_fm": {
  "command": "rtl_fm",
  "args": [
    "-f", "168.075M",    // Frequenz
    "-p", "30",          // PPM-Korrektur
    "-g", "100",         // Gain
    "-s", "22050",       // Sample-Rate
    "-l", "1"            // Squelch-Level
  ]
}
```

### Multimon-NG Parameter
```json
"multimon": {
  "command": "multimon-ng",
  "args": [
    "-t", "raw",              // Input-Format
    "-a", "POCSAG512",        // POCSAG 512 Baud
    "-a", "POCSAG1200",       // POCSAG 1200 Baud
    "-a", "POCSAG2400",       // POCSAG 2400 Baud
    "--timestamp",            // Zeitstempel hinzufügen
    "-p", "-u", "-n",         // Output-Optionen
    "-f", "auto"              // Auto-Frequenzerkennung
  ]
}
```

### WebSocket-Konfiguration
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
    "config_updated": "config.updated",
    "command_received": "command.execute"
  }
}
```

## Best Practices

### Code-Organisation
- ✅ Worker in separaten Files
- ✅ Handler in separaten Files
- ✅ Klare Verantwortlichkeiten
- ✅ Logging durchgängig
- ✅ Error-Handling überall

### Sicherheit
- Token nicht in Git committen
- systemd Service mit eingeschränkten Rechten
- Read-only Home-Directory (außer logs/messages)
- Virtual Environment für Python-Isolation

### Deployment
- Automatische Installation via install.sh
- Automatische Updates via update.sh
- Backup vor jedem Update
- Rollback-Möglichkeit

## Debugging

### Logs prüfen
```bash
# Service-Logs
sudo journalctl -u noxfeed -f

# Log-Datei
tail -f /home/nox/noxfeed/logs/noxfeed.log

# Console-Mode (für Testing)
cd /home/nox/noxfeed
source venv/bin/activate
python3 noxfeed.py -l console
```

### Empfangene Nachrichten prüfen
```bash
# Heutige Nachrichten
cat /home/nox/noxfeed/messages/$(date +%Y%m%d).json | jq .

# Letzte 10 Nachrichten
cat /home/nox/noxfeed/messages/$(date +%Y%m%d).json | jq '.[-10:]'
```

### WebSocket-Verbindung testen
Logs zeigen WebSocket-Events:
```
WebSocket connected to Reverb: nox.lwyrup.at
Reverb connection established
Successfully subscribed to channel: config-updates
Successfully subscribed to channel: commands
```

## Wartung

### Update durchführen
```bash
cd /home/nox/noxfeed
sudo ./update.sh
```

### Service neustarten
```bash
sudo systemctl restart noxfeed
```

### Konfiguration ändern
```bash
sudo nano /home/nox/noxfeed/config/config.json
sudo systemctl restart noxfeed
```

### Remote-Update via API
Sende Command über Laravel:
```php
broadcast(new CommandEvent([
    'command' => 'update',
    'params' => []
]))->toOthers();
```
