#!/usr/bin/env python3
import requests
from typing import Optional, Dict, Any
import json
import sys
import setproctitle
from includes.api.laravel_api_client import LaravelAPIClient
from includes.config import Config


# Hauptprogramm
if __name__ == "__main__":
    try:
        # Konfiguration laden
        config = Config()
        
        # Prozessname setzen, damit er in ps -A als "noxfeed" angezeigt wird
        setproctitle.setproctitle(config.process_name)
        
        # API Client mit Konfiguration initialisieren
        api = LaravelAPIClient(
            base_url=config.api_base_url,
            api_token=config.api_token if config.api_token else None
        )
        
        print(f"NoxFeed gestartet - Verbinde zu {config.api_base_url}")
        print(f"Max Retries: {config.api_max_retries}, Timeout: {config.api_timeout}s")
        
        # Beispiel: Alle Benutzer abrufen
        users = api.get('/users')
        print("Benutzer:", json.dumps(users, indent=2))
        
        # Beispiel: Neuen Benutzer erstellen
        new_user = api.post('/users', {
            'name': 'Max Mustermann',
            'email': 'max@example.com',
            'password': 'sicher123'
        })
        print("Neuer Benutzer:", json.dumps(new_user, indent=2))
        
        # Beispiel: Benutzer aktualisieren
        updated_user = api.put('/users/1', {
            'name': 'Max Mustermann Updated'
        })
        print("Aktualisierter Benutzer:", json.dumps(updated_user, indent=2))
        
        # Beispiel: Benutzer löschen
        result = api.delete('/users/1')
        print("Gelöscht:", json.dumps(result, indent=2))
        
    except FileNotFoundError as e:
        print(f"Fehler: {e}")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Fehler: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Fehler: {e}")
        sys.exit(1)