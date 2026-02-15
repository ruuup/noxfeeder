import requests
from typing import Optional, Dict, Any


class LaravelAPIClient:
    """Client for communicating with a Laravel API."""

    def __init__(self, base_url: str, api_token: Optional[str] = None):
        """
        Initializes the API client.

        Args:
            base_url: Base URL of the Laravel API (e.g. 'https://api.example.com')
            api_token: Optional bearer token for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

        if api_token:
            self.session.headers.update({"Authorization": f"Bearer {api_token}"})

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        GET request to the API.

        Args:
            endpoint: API endpoint (e.g. '/users' or '/posts/1')
            params: Optional query parameters

        Returns:
            JSON response as a dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST request to the API.

        Args:
            endpoint: API endpoint
            data: Data to send

        Returns:
            JSON response as a dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        PUT request to the API.

        Args:
            endpoint: API endpoint
            data: Data to update

        Returns:
            JSON response as a dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        DELETE request to the API.

        Args:
            endpoint: API endpoint

        Returns:
            JSON response as a dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url)
        response.raise_for_status()
        return response.json()
