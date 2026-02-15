from typing import Dict, Any
from .laravel_api_client import LaravelAPIClient


class LoggingAPI:
    """Logging API (create only)."""

    def __init__(self, client: LaravelAPIClient, base_path: str = ""):
        """
        Args:
            client: Shared LaravelAPIClient
            base_path: Optional base path for logging endpoints (e.g. '/logs')
        """
        self.client = client
        self.base_path = base_path.rstrip('/')

    def _path(self, resource: str) -> str:
        resource_path = resource if resource.startswith('/') else f"/{resource}"
        return f"{self.base_path}{resource_path}"

    def create(self, resource: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.post(self._path(resource), data)
