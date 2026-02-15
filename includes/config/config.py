#!/usr/bin/env python3
import json
import os
from typing import Any, Dict


class Config:
    """Configuration class for loading and managing config.json."""

    def __init__(self, config_path: str = "config/config.json"):
        """
        Initializes the configuration.

        Args:
            config_path: Path to the config.json file
        """
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Loads the configuration from the JSON file.

        Returns:
            Dictionary with configuration values
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing configuration file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a value from the configuration.

        Args:
            key: Key in the format 'section.key' (e.g. 'api.base_url')
            default: Default value if the key does not exist

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    @property
    def api_base_url(self) -> str:
        """API base URL."""
        return self.get("api.base_url", "")

    @property
    def api_token(self) -> str:
        """API token."""
        return self.get("api.token", "")

    @property
    def api_timeout(self) -> int:
        """API timeout in seconds."""
        return self.get("api.timeout", 30)

    @property
    def api_max_retries(self) -> int:
        """Maximum number of retries."""
        return self.get("api.max_retries", 3)

    @property
    def api_retry_delay(self) -> int:
        """Delay between retries in seconds."""
        return self.get("api.retry_delay", 5)

    @property
    def logging_enabled(self) -> bool:
        """Logging enabled."""
        return self.get("logging.enabled", True)

    @property
    def logging_level(self) -> str:
        """Logging level."""
        return self.get("logging.level", "INFO")

    @property
    def logging_file(self) -> str:
        """Log file path."""
        return self.get("logging.log_file", "logs/noxfeed.log")

    @property
    def process_name(self) -> str:
        """Process name."""
        return self.get("process.name", "noxfeed")

    @property
    def process_daemon(self) -> bool:
        """Run as daemon."""
        return self.get("process.daemon", False)

    def reload(self) -> None:
        """Reloads the configuration."""
        self._config = self._load_config()

    def update_from_dict(self, new_config: Dict[str, Any]) -> None:
        """Updates the in-memory configuration from a dictionary."""
        if isinstance(new_config, dict):
            self._config = new_config

    def save(self) -> None:
        """Persists the current configuration to disk."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2)

    def __repr__(self) -> str:
        return f"Config(config_path='{self.config_path}')"
