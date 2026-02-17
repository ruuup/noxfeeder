import os
import sys
import subprocess
from typing import Optional, Dict, Any
import logging


class CommandHandler:
    """Handler for processing remote commands (restart, update)."""

    def __init__(
        self,
        install_dir: str = "/home/nox/noxfeed",
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.install_dir = install_dir
        self.logger = logger

    def handle_command(
        self, command: str, params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Handle a command received from API or WebSocket.

        Supported commands:
        - restart: Restart the application
        - update: Pull latest changes and restart
        - reload_config: Reload configuration
        """
        if self.logger:
            self.logger.info("Received command: %s with params: %s", command, params)

        try:
            if command == "restart":
                return self._restart()
            elif command == "update":
                return self._update()
            elif command == "reload_config":
                return True  # Handled by config update mechanism
            else:
                if self.logger:
                    self.logger.warning("Unknown command: %s", command)
                return False
        except Exception as e:
            if self.logger:
                self.logger.error("Failed to execute command %s: %s", command, e)
            return False

    def _restart(self) -> bool:
        """Restart the application via systemd."""
        if self.logger:
            self.logger.info("Executing restart command...")

        try:
            # Restart via systemd
            subprocess.run(
                ["sudo", "systemctl", "restart", "noxfeed"],
                check=False,
                timeout=5,
            )
            return True
        except Exception as e:
            if self.logger:
                self.logger.error("Restart failed: %s", e)
            return False

    def _update(self) -> bool:
        """Execute update script and restart."""
        if self.logger:
            self.logger.info("Executing update command...")

        update_script = os.path.join(self.install_dir, "update.sh")

        if not os.path.exists(update_script):
            if self.logger:
                self.logger.error("Update script not found: %s", update_script)
            return False

        try:
            # Execute update script in background
            subprocess.Popen(
                ["sudo", update_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            if self.logger:
                self.logger.info("Update script started")

            return True
        except Exception as e:
            if self.logger:
                self.logger.error("Update failed: %s", e)
            return False
