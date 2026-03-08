import json
import threading
import time
import ssl
import socket as sock
from datetime import datetime
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
        api_client=None,
        host: str = "nox.lwyrup.at",
        port: int = 443,
        secure: bool = True,
        token: Optional[str] = None,
        reconnect_delay: int = 5,
        heartbeat_interval: int = 15,
        monitoring_interval: int = 30,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.app_key = app_key
        self.channel = channel
        self.event_name = event_name
        self.on_event = on_event
        self.api_client = api_client
        self.host = host
        self.port = port
        self.secure = secure
        self.token = token
        self.reconnect_delay = reconnect_delay
        self.heartbeat_interval = heartbeat_interval
        self.monitoring_interval = monitoring_interval
        self.logger = logger
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._monitoring_thread: Optional[threading.Thread] = None
        self._ws: Optional[websocket.WebSocketApp] = None
        self._connected = False
        self._socket_id: Optional[str] = None

        # Client identification for monitoring
        self.client_id = f"noxfeed-{sock.gethostname()}"
        self.client_name = "NoxFeed Python Client"
        self.hostname = sock.gethostname()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        if self.logger:
            self.logger.info(
                "Starting WebSocket listener for channel: %s", self.channel
            )
            self.logger.debug("WebSocket URL: %s", self._build_url())
            self.logger.debug("WebSocket Auth: %s", "Yes" if self.token else "No")

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

        # Start Pusher heartbeat thread
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True
        )
        self._heartbeat_thread.start()

        # Start monitoring heartbeat thread (for feeder status)
        if self.api_client:
            self._monitoring_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True
            )
            self._monitoring_thread.start()

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
            try:
                if self.logger:
                    self.logger.debug(
                        "Attempting WebSocket connection to %s", self.host
                    )

                self._ws = websocket.WebSocketApp(
                    self._build_url(),
                    header=self._headers(),
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )

                # SSL options for wss:// connections
                sslopt = None
                if self.secure:
                    sslopt = {"cert_reqs": ssl.CERT_NONE}

                self._ws.run_forever(sslopt=sslopt)

            except Exception as e:
                if self.logger:
                    self.logger.error(
                        "WebSocket thread exception: %s", e, exc_info=True
                    )

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
        # Log all incoming messages for debugging
        if self.logger:
            self.logger.debug("WS << %s", message)

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
            # Extract socket_id for channel auth
            data = payload.get("data")
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    pass
            if isinstance(data, dict):
                self._socket_id = data.get("socket_id")

            if self.logger:
                self.logger.info(
                    "Reverb connection established (socket_id: %s)", self._socket_id
                )

            # Register with monitoring system
            if self.api_client:
                self._track_noxfeed_client(announce=True)

            # Subscribe to the channel
            self._subscribe()

        elif (
            event == "pusher:subscription_succeeded"
            or event == "pusher_internal:subscription_succeeded"
        ):
            if self.logger:
                self.logger.info("Successfully subscribed to channel: %s", self.channel)

        elif event == "pusher:ping":
            # Respond to server ping with pong
            self._send_pong()

        elif event == "pusher:pong":
            # Response to our heartbeat ping - this is expected
            if self.logger:
                self.logger.debug("Received pong from server")

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

        else:
            # Log unknown events
            if self.logger:
                self.logger.info("Unknown WebSocket event: %s", event)

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

        # For private/presence channels, get auth from Laravel
        if self.channel.startswith("private-") or self.channel.startswith("presence-"):
            if not self._socket_id:
                if self.logger:
                    self.logger.error(
                        "Cannot subscribe to private channel: no socket_id"
                    )
                return

            auth = self._get_channel_auth(self._socket_id, self.channel)
            if not auth:
                if self.logger:
                    self.logger.error("Failed to get channel auth for %s", self.channel)
                return

            subscribe_msg["data"]["auth"] = auth

        if self.logger:
            self.logger.info("Subscribing to channel: %s", self.channel)
            self.logger.debug("WS >> %s", json.dumps(subscribe_msg))

        self._ws.send(json.dumps(subscribe_msg))

    def _send_pong(self) -> None:
        """Respond to Reverb ping with pong message."""
        if not self._ws:
            return

        pong_msg = {"event": "pusher:pong", "data": {}}
        self._ws.send(json.dumps(pong_msg))

        if self.logger:
            self.logger.debug("Sent pong response to Reverb")

    def _get_channel_auth(self, socket_id: str, channel_name: str) -> Optional[str]:
        """Get channel authentication from Laravel /broadcasting/auth endpoint."""
        if not self.api_client:
            return None

        try:
            # Use requests session from api_client
            headers = {
                "Authorization": f"Bearer {self.api_client.token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            # Build auth URL (remove /api from base_url if present)
            base_url = self.api_client.base_url.replace("/api", "")
            auth_url = f"{base_url}/broadcasting/auth"

            response = self.api_client.session.post(
                auth_url,
                json={"socket_id": socket_id, "channel_name": channel_name},
                headers=headers,
                timeout=10,
            )

            if response.status_code != 200:
                if self.logger:
                    self.logger.error(
                        "Channel auth failed %s: %s",
                        response.status_code,
                        response.text,
                    )
                return None

            data = response.json()
            auth_token = data.get("auth")

            if self.logger:
                self.logger.debug("Channel auth successful for %s", channel_name)

            return auth_token

        except Exception as e:
            if self.logger:
                self.logger.error("Exception during channel auth: %s", e)
            return None

    def _track_noxfeed_client(self, announce: bool = False) -> bool:
        """Register/update this client in the monitoring system."""
        if not self.api_client:
            return False

        try:
            payload = {
                "client_id": self.client_id,
                "client_name": self.client_name,
                "user": self.api_client.user,
                "password": self.api_client.password,
                "metadata": {
                    "hostname": self.hostname,
                    "email": self.api_client.user,
                    "connected_at": datetime.now().isoformat(),
                },
            }

            response = self.api_client.session.post(
                f"{self.api_client.base_url}/websocket/track/noxfeed-client",
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                if announce and self.logger:
                    self.logger.info(
                        "Monitoring registration successful: %s", self.client_id
                    )
                return True

            if announce and self.logger:
                self.logger.error(
                    "Monitoring registration failed %s: %s",
                    response.status_code,
                    response.text,
                )
            return False

        except Exception as e:
            if announce and self.logger:
                self.logger.error("Monitoring track exception: %s", e)
            return False

    def _monitoring_loop(self) -> None:
        """Send monitoring heartbeat to keep feeder status as online."""
        # Wait a bit before starting to ensure connection is established
        time.sleep(5)

        while not self._stop_event.is_set():
            if self._connected:
                try:
                    self._track_noxfeed_client(announce=False)
                except Exception as e:
                    if self.logger:
                        self.logger.warning("Monitoring heartbeat failed: %s", e)

            time.sleep(self.monitoring_interval)

    def _heartbeat_loop(self) -> None:
        """Send heartbeat to server every interval to keep connection alive."""
        while not self._stop_event.is_set():
            time.sleep(self.heartbeat_interval)
            if self._connected and self._ws:
                try:
                    # Send ping to server
                    ping_msg = {"event": "pusher:ping", "data": {}}
                    self._ws.send(json.dumps(ping_msg))
                    if self.logger:
                        self.logger.debug("Sent heartbeat ping to Reverb")
                except Exception as e:
                    if self.logger:
                        self.logger.warning("Failed to send heartbeat: %s", e)

    def _on_error(self, ws, error: Exception) -> None:
        if self.logger:
            self.logger.error("WebSocket error: %s", error)

    def _on_close(self, ws, status_code, msg) -> None:
        self._connected = False
        if self.logger:
            self.logger.info("WebSocket closed: %s %s", status_code, msg)
