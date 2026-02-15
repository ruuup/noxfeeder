import json
import threading
import time
from typing import Callable, Optional, Dict, Any
import websocket
import logging


class LaravelWebSocketListener:
    """WebSocket listener for Laravel Reverb (Pusher protocol compatible)."""

    def __init__(
        self,
        app_key: str,
        channel: str,
        event_name: str,
        on_event: Callable[[Dict[str, Any]], None],
        host: str = "nox.lwyrup.at",
        port: int = 443,
        secure: bool = True,
        token: Optional[str] = None,
        reconnect_delay: int = 5,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.app_key = app_key
        self.channel = channel
        self.event_name = event_name
        self.on_event = on_event
        self.host = host
        self.port = port
        self.secure = secure
        self.token = token
        self.reconnect_delay = reconnect_delay
        self.logger = logger
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._ws: Optional[websocket.WebSocketApp] = None
        self._connected = False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._ws:
            self._ws.close()

    def _build_url(self) -> str:
        """Build Reverb/Pusher compatible WebSocket URL."""
        protocol = "wss" if self.secure else "ws"
        url = f"{protocol}://{self.host}"
        if (self.secure and self.port != 443) or (not self.secure and self.port != 80):
            url += f":{self.port}"
        url += f"/app/{self.app_key}?protocol=7&client=python&version=1.0.0"
        return url

    def _headers(self) -> Optional[list]:
        if not self.token:
            return None
        return [f"Authorization: Bearer {self.token}"]

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._ws = websocket.WebSocketApp(
                self._build_url(),
                header=self._headers(),
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )
            self._ws.run_forever()

            if self._stop_event.is_set():
                break

            if self.logger:
                self.logger.warning(
                    "WebSocket disconnected. Reconnecting in %ss...",
                    self.reconnect_delay,
                )
            time.sleep(self.reconnect_delay)

    def _on_open(self, ws) -> None:
        if self.logger:
            self.logger.info("WebSocket connected to Reverb: %s", self.host)

    def _on_message(self, ws, message: str) -> None:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            if self.logger:
                self.logger.warning("Non-JSON WebSocket message: %s", message)
            return

        event = payload.get("event")

        # Handle Pusher/Reverb protocol events
        if event == "pusher:connection_established":
            self._connected = True
            if self.logger:
                self.logger.info("Reverb connection established")
            # Subscribe to the channel
            self._subscribe()

        elif event == "pusher:subscription_succeeded":
            if self.logger:
                self.logger.info("Successfully subscribed to channel: %s", self.channel)

        elif event == "pusher:error":
            if self.logger:
                self.logger.error("Reverb error: %s", payload.get("data"))

        elif event == self.event_name:
            # Handle the actual event we're listening for
            data = payload.get("data", {})
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    pass
            self.on_event(
                {"event": event, "data": data, "channel": payload.get("channel")}
            )

    def _subscribe(self) -> None:
        """Subscribe to a channel using Pusher protocol."""
        if not self._ws:
            return

        subscribe_msg = {
            "event": "pusher:subscribe",
            "data": {
                "channel": self.channel,
            },
        }

        # Add auth if token is provided (for private/presence channels)
        if self.token and (
            self.channel.startswith("private-") or self.channel.startswith("presence-")
        ):
            subscribe_msg["data"]["auth"] = self.token

        if self.logger:
            self.logger.debug("Subscribing to channel: %s", self.channel)

        self._ws.send(json.dumps(subscribe_msg))

    def _on_error(self, ws, error: Exception) -> None:
        if self.logger:
            self.logger.error("WebSocket error: %s", error)

    def _on_close(self, ws, status_code, msg) -> None:
        self._connected = False
        if self.logger:
            self.logger.info("WebSocket closed: %s %s", status_code, msg)
