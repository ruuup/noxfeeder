# Laravel API & WebSocket Spezifikation für NoxFeed Python Client

## API Endpoints

### 1. Login (Erstanmeldung)
**POST** `/api/auth/token`

Request:
```json
{
  "user": "feeder1@api.local",
  "password": "gh95q1IOxRzNQ6DYH2GB",
  "token_name": "python-client"
}
```

Response:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_at": "2026-03-18T10:00:00+00:00",
  "user": {
    "id": 1,
    "email": "feeder1@api.local"
  }
}
```

- Token-Lifetime: **10 Tage**
- Format: Bearer Token
- expires_at: ISO 8601 mit Timezone

---

### 2. Token Renewal
**POST** `/api/auth/renew`

Headers:
```
Authorization: Bearer {token}
```

Response:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_at": "2026-03-18T10:00:00+00:00"
}
```

- Client erneuert Token **1 Stunde vor Ablauf**
- Bei Fehler: Fallback auf `/auth/token` (neuer Login)

---

### 3. POCSAG Nachricht senden
**POST** `/api/message`

Headers:
```
Authorization: Bearer {token}
Content-Type: application/json
```

Request:
```json
{
  "timestamp": "2026-03-08T14:23:45.123456",
  "ric": "1234567",
  "subric": "3",
  "message": "This is a test message"
}
```

Felder:
- `timestamp` (string, ISO 8601): Empfangszeitpunkt
- `ric` (string): Receiver Identity Code (POCSAG Address)
- `subric` (string): Function Code (0-3)
- `message` (string): Nachrichteninhalt

Response:
```json
{
  "success": true,
  "message_id": 12345
}
```

---

### 4. Konfiguration abrufen (Optional)
**GET** `/api/config`

Headers:
```
Authorization: Bearer {token}
```

Response: Komplette Config als JSON

---

## WebSocket (Laravel Reverb / Pusher Protocol)

### Verbindung
```
URL: wss://nox.lwyrup.at:443/app/{app_key}?protocol=7&client=python&version=1.0.0
App Key: uu5cwxbjivil6ykji9qu
Header: Authorization: Bearer {token}
```

**Wichtig:** WebSocket nutzt den gleichen Token wie die API!

---

### Channels

#### Channel: `message` (Public)
Event: `message.sent`

Payload:
```json
{
  "event": "message.sent",
  "channel": "message",
  "data": {
    "timestamp": "2026-03-08T14:23:45.123456",
    "ric": "1234567",
    "subric": "3",
    "message": "This is a test message"
  }
}
```

#### Channel: `config` (Public)
Event: `config.updated`

Payload:
```json
{
  "event": "config.updated",
  "channel": "config",
  "data": {
    "config_url": "/api/config"
  }
}
```

Client fetched dann neue Config via GET /api/config

---

### Pusher Protocol Events

#### Server → Client:
1. **Connection Established**
```json
{"event": "pusher:connection_established", "data": "{\"socket_id\":\"123.456\"}"}
```

2. **Subscription Success**
```json
{"event": "pusher:subscription_succeeded", "channel": "message"}
```

3. **Server Ping**
```json
{"event": "pusher:ping", "data": {}}
```

4. **Error**
```json
{"event": "pusher:error", "data": {"code": 4201, "message": "Pong reply not received in time"}}
```

#### Client → Server:
1. **Subscribe**
```json
{"event": "pusher:subscribe", "data": {"channel": "message"}}
```

2. **Pong**
```json
{"event": "pusher:pong", "data": {}}
```

3. **Heartbeat** (alle 15 Sekunden)
```json
{"event": "pusher:ping", "data": {}}
```

---

## Client Verhalten

### Startup-Sequenz:
1. Login: POST /api/auth/token mit user/password
2. Token speichern in config.json (wenn config.persist: true)
3. WebSocket verbinden mit Bearer Token
4. Subscribe zu Channels: "message" und "config"
5. Heartbeat-Thread starten (Ping alle 15 Sekunden)

### Laufzeit:
- **Token Check:** Vor jedem API-Call prüfen ob Token < 1h gültig
- **Token Renewal:** Bei < 1h: POST /api/auth/renew
- **Message Flow:** RTL-SDR → Multimon-NG → Parser → POST /api/message
- **Heartbeat:** Alle 15s pusher:ping senden
- **Pong Response:** Auf Server pusher:ping mit pusher:pong antworten

### Bei Fehler:
- **WebSocket Disconnect:** Auto-Reconnect nach 5 Sekunden
- **Token Renewal Failed:** Fallback auf neuen Login (POST /auth/token)
- **API Errors:** Logging mit Details

---

## Laravel Implementation Beispiel

### Message Event Broadcasting:
```php
namespace App\Events;

use Illuminate\Broadcasting\Channel;
use Illuminate\Contracts\Broadcasting\ShouldBroadcast;

class MessageSentEvent implements ShouldBroadcast
{
    public function __construct(
        public string $timestamp,
        public string $ric,
        public string $subric,
        public string $message
    ) {}

    public function broadcastOn(): Channel
    {
        return new Channel('message');
    }

    public function broadcastAs(): string
    {
        return 'message.sent';
    }
}
```

### Message Controller:
```php
public function store(Request $request)
{
    $validated = $request->validate([
        'timestamp' => 'required|string',
        'ric' => 'required|string',
        'subric' => 'required|string',
        'message' => 'required|string',
    ]);

    $message = Message::create($validated);

    broadcast(new MessageSentEvent(
        $validated['timestamp'],
        $validated['ric'],
        $validated['subric'],
        $validated['message']
    ));

    return response()->json([
        'success' => true,
        'message_id' => $message->id
    ]);
}
```

---

## Zusammenfassung

- **Auth:** Token-basiert, 10 Tage gültig, auto-renewal 1h vor Ablauf
- **API Format:** timestamp, ric, subric, message
- **WebSocket:** Pusher Protocol v7, Channels: message + config
- **Heartbeat:** 15 Sekunden Client-Ping
- **Reconnect:** Automatisch nach 5s bei Verbindungsabbruch
- **Logging:** Alle Fehler werden geloggt (API, WebSocket, Token)
