"""Compatibility shim. API code now lives under includes/api."""

from includes.api.laravel_api_client import LaravelAPIClient

__all__ = ["LaravelAPIClient"]
