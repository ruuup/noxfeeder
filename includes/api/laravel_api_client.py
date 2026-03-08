import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging


class LaravelAPIClient:
    """Client for communicating with a Laravel API with token-based authentication."""

    def __init__(
        self,
        base_url: str,
        api_token: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initializes the API client.

        Args:
            base_url: Base URL of the Laravel API (e.g. 'https://api.example.com')
            api_token: Optional bearer token for authentication
            user: Optional username/email for login authentication
            password: Optional password for login authentication
            logger: Optional logger instance
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.user = user
        self.password = password
        self.logger = logger
        self.token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        # Set default headers
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

        if api_token:
            self.set_token(api_token)

    def set_token(self, token: str, expires_at: Optional[str] = None) -> None:
        """
        Set or update the bearer token.

        Args:
            token: Bearer token string
            expires_at: Optional ISO 8601 datetime string for token expiry
        """
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

        if expires_at:
            try:
                # Parse ISO 8601 datetime (e.g., "2026-03-17T10:00:00+00:00")
                self.token_expires_at = datetime.fromisoformat(
                    expires_at.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                self.token_expires_at = None
                if self.logger:
                    self.logger.warning("Failed to parse token expiry: %s", expires_at)

    def login(self, token_name: str = "python-client") -> Dict[str, Any]:
        """
        Authenticate with username/password and obtain a bearer token.

        Args:
            token_name: Name for the generated token

        Returns:
            Login response with token, expires_at, and user info

        Raises:
            ValueError: If user/password not configured
            requests.HTTPError: If authentication fails
        """
        if not self.user or not self.password:
            raise ValueError("User and password must be configured for login")

        if self.logger:
            self.logger.info("Authenticating with API as %s", self.user)

        # Don't use Bearer token for login request
        headers = self.session.headers.copy()
        if "Authorization" in headers:
            del headers["Authorization"]

        response = requests.post(
            f"{self.base_url}/auth/token",
            json={
                "user": self.user,
                "password": self.password,
                "token_name": token_name,
            },
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()

        # Update token and expiry
        self.set_token(data.get("token"), data.get("expires_at"))

        if self.logger:
            self.logger.info(
                "Successfully authenticated. Token expires at: %s",
                self.token_expires_at,
            )

        # Callback for token updates (can be used to persist token)
        if hasattr(self, 'on_token_updated') and callable(self.on_token_updated):
            self.on_token_updated(self.token, self.token_expires_at)

        return data

    def renew_token(self) -> Dict[str, Any]:
        """
        Renew the current bearer token before it expires.

        Returns:
            Renewal response with new token and expiry

        Raises:
            requests.HTTPError: If renewal fails
        """
        if self.logger:
            self.logger.info("Renewing authentication token")

        response = self.session.post(f"{self.base_url}/auth/renew")
        response.raise_for_status()

        data = response.json()

        # Update token and expiry
        self.set_token(data.get("token"), data.get("expires_at"))

        if self.logger:
            self.logger.info(
                "Token renewed successfully. New expiry: %s", self.token_expires_at
            )

        # Callback for token updates (can be used to persist token)
        if hasattr(self, 'on_token_updated') and callable(self.on_token_updated):
            self.on_token_updated(self.token, self.token_expires_at)

        return data

    def is_token_expired(self, buffer_seconds: int = 3600) -> bool:
        """
        Check if the token is expired or will expire soon.

        Args:
            buffer_seconds: Renew token if it expires within this many seconds (default: 1 hour)

        Returns:
            True if token is missing, expired, or expires within buffer time
        """
        if not self.token or not self.token_expires_at:
            return True

        # Check if token expires within buffer period
        now = datetime.now(self.token_expires_at.tzinfo)
        expires_soon = self.token_expires_at <= now + timedelta(seconds=buffer_seconds)

        return expires_soon

    def ensure_authenticated(self) -> None:
        """
        Ensure we have a valid authentication token.
        Logs in if no token exists, or renews if token is expired/expiring soon.

        Raises:
            ValueError: If authentication is not configured
            requests.HTTPError: If authentication fails
        """
        if self.is_token_expired():
            if not self.token:
                # No token yet, perform initial login
                self.login()
            else:
                # Token exists but expired/expiring, renew it
                try:
                    self.renew_token()
                except requests.HTTPError as e:
                    # If renewal fails (e.g., token already expired), try login
                    if self.logger:
                        self.logger.warning(
                            "Token renewal failed (%s), attempting fresh login", e
                        )
                    self.login()

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        GET request to the API.

        Args:
            endpoint: API endpoint (e.g. '/users' or '/posts/1')
            params: Optional query parameters

        Returns:
            JSON response as a dictionary
        """
        # Ensure we have a valid token if user/password configured
        if self.user and self.password:
            self.ensure_authenticated()

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
        # Ensure we have a valid token if user/password configured
        if self.user and self.password:
            self.ensure_authenticated()

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
        # Ensure we have a valid token if user/password configured
        if self.user and self.password:
            self.ensure_authenticated()

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
        # Ensure we have a valid token if user/password configured
        if self.user and self.password:
            self.ensure_authenticated()

        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url)
        response.raise_for_status()
        return response.json()
