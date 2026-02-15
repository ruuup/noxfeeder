from typing import Optional, Dict, Any
from .laravel_api_client import LaravelAPIClient


class ConfigurationAPI:
    """CRUD API for configurations."""

    def __init__(self, client: LaravelAPIClient, base_path: str = ""):
        """
        Args:
            client: Shared LaravelAPIClient
            base_path: Optional base path for configuration endpoints (e.g. '/configurations')
        """
        self.client = client
        self.base_path = base_path.rstrip("/")

    def _path(self, resource: str) -> str:
        resource_path = resource if resource.startswith("/") else f"/{resource}"
        return f"{self.base_path}{resource_path}"

    def list(self, resource: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        return self.client.get(self._path(resource), params=params)

    def get(self, resource: str, item_id: Any) -> Dict[str, Any]:
        return self.client.get(self._path(f"{resource}/{item_id}"))

    def create(self, resource: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.post(self._path(resource), data)

    def update(
        self, resource: str, item_id: Any, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self.client.put(self._path(f"{resource}/{item_id}"), data)

    def delete(self, resource: str, item_id: Any) -> Dict[str, Any]:
        return self.client.delete(self._path(f"{resource}/{item_id}"))
