# NoxFeeder

RTL-SDR data processor with Laravel Reverb WebSocket integration.

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
