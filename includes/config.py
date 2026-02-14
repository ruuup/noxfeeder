#!/usr/bin/env python3
import json
import os
from typing import Any, Dict


class Config:
    """Konfigurationsklasse zum Laden und Verwalten der config.json"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialisiert die Konfiguration
        
        Args:
            config_path: Pfad zur config.json Datei
        """
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Lädt die Konfiguration aus der JSON-Datei
        
        Returns:
            Dictionary mit Konfigurationswerten
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Fehler beim Parsen der Konfigurationsdatei: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Holt einen Wert aus der Konfiguration
        
        Args:
            key: Schlüssel im Format 'section.key' (z.B. 'api.base_url')
            default: Standardwert falls Schlüssel nicht existiert
            
        Returns:
            Konfigurationswert oder default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def api_base_url(self) -> str:
        """API Base URL"""
        return self.get('api.base_url', '')
    
    @property
    def api_token(self) -> str:
        """API Token"""
        return self.get('api.token', '')
    
    @property
    def api_timeout(self) -> int:
        """API Timeout in Sekunden"""
        return self.get('api.timeout', 30)
    
    @property
    def api_max_retries(self) -> int:
        """Maximale Anzahl an Wiederholungsversuchen"""
        return self.get('api.max_retries', 3)
    
    @property
    def api_retry_delay(self) -> int:
        """Wartezeit zwischen Wiederholungsversuchen in Sekunden"""
        return self.get('api.retry_delay', 5)
    
    @property
    def logging_enabled(self) -> bool:
        """Logging aktiviert"""
        return self.get('logging.enabled', True)
    
    @property
    def logging_level(self) -> str:
        """Logging Level"""
        return self.get('logging.level', 'INFO')
    
    @property
    def logging_file(self) -> str:
        """Log-Datei Pfad"""
        return self.get('logging.log_file', 'logs/noxfeed.log')
    
    @property
    def process_name(self) -> str:
        """Prozessname"""
        return self.get('process.name', 'noxfeed')
    
    @property
    def process_daemon(self) -> bool:
        """Als Daemon ausführen"""
        return self.get('process.daemon', False)
    
    def reload(self) -> None:
        """Lädt die Konfiguration neu"""
        self._config = self._load_config()
    
    def __repr__(self) -> str:
        return f"Config(config_path='{self.config_path}')"