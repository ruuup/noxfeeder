import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import logging


class MessageHandler:
    """Handler for processing received POCSAG messages."""

    def __init__(
        self,
        storage_dir: str = "messages",
        api_client=None,
        api_endpoint: str = "/messages",
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.storage_dir = storage_dir
        self.api_client = api_client
        self.api_endpoint = api_endpoint
        self.logger = logger
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """Ensure the storage directory exists."""
        os.makedirs(self.storage_dir, exist_ok=True)

    def parse_pocsag_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a POCSAG line from multimon-ng output.

        Example format:
        POCSAG1200: Address: 1234567  Function: 3  Alpha:   This is a test message
        """
        if not line or "POCSAG" not in line:
            return None

        try:
            parts = line.split(":", 1)
            if len(parts) < 2:
                return None

            protocol = parts[0].strip()
            content = parts[1].strip()

            # Extract address
            address = None
            if "Address:" in content:
                addr_parts = content.split("Address:", 1)[1].split("Function:", 1)
                if addr_parts:
                    address = addr_parts[0].strip()

            # Extract function
            function = None
            if "Function:" in content:
                func_parts = content.split("Function:", 1)[1].split("Alpha:", 1)
                if not func_parts:
                    func_parts = content.split("Function:", 1)[1].split("Numeric:", 1)
                if func_parts:
                    function = func_parts[0].strip()

            # Extract message type and content
            message_type = "alpha"
            message = ""

            if "Alpha:" in content:
                message_type = "alpha"
                message = content.split("Alpha:", 1)[1].strip()
            elif "Numeric:" in content:
                message_type = "numeric"
                message = content.split("Numeric:", 1)[1].strip()

            return {
                "protocol": protocol,
                "address": address,
                "function": function,
                "type": message_type,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "raw": line,
            }

        except Exception as e:
            if self.logger:
                self.logger.error("Failed to parse POCSAG line: %s - %s", line, e)
            return None

    def save_local(self, message_data: Dict[str, Any]) -> str:
        """Save message to local JSON file."""
        timestamp = datetime.now()
        filename = f"{timestamp.strftime('%Y%m%d')}.json"
        filepath = os.path.join(self.storage_dir, filename)

        messages = []
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    messages = json.load(f)
            except (json.JSONDecodeError, IOError):
                messages = []

        messages.append(message_data)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)

            if self.logger:
                self.logger.debug("Message saved locally: %s", filepath)

            return filepath
        except IOError as e:
            if self.logger:
                self.logger.error("Failed to save message locally: %s", e)
            raise

    def send_to_api(self, message_data: Dict[str, Any]) -> bool:
        """Send message to Laravel API."""
        if not self.api_client:
            if self.logger:
                self.logger.warning("No API client configured, skipping API send")
            return False

        try:
            response = self.api_client.post(self.api_endpoint, message_data)

            if self.logger:
                self.logger.info("Message sent to API: %s", message_data.get("address"))

            return True
        except Exception as e:
            if self.logger:
                self.logger.error("Failed to send message to API: %s", e)
            return False

    def process_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Process a line from multimon-ng output.

        Returns the parsed message data if it was a POCSAG message, None otherwise.
        """
        message_data = self.parse_pocsag_line(line)

        if not message_data:
            return None

        if self.logger:
            self.logger.info(
                "POCSAG message received - Address: %s, Type: %s, Message: %s",
                message_data.get("address"),
                message_data.get("type"),
                message_data.get("message", "")[:50],  # First 50 chars
            )

        # Save locally
        try:
            self.save_local(message_data)
        except Exception as e:
            if self.logger:
                self.logger.error("Failed to save message locally: %s", e)

        # Send to API
        self.send_to_api(message_data)

        return message_data
