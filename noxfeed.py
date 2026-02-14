#!/usr/bin/env python3
import requests
from typing import Optional, Dict, Any
import json
import sys
import setproctitle
from includes.api.laravel_api_client import LaravelAPIClient


# Beispiel Verwendung
if __name__ == "__main__":
    # Prozessname setzen, damit er in ps -A als "noxfeed" angezeigt wird
    setproctitle.setproctitle('noxfeed')
    
    # API Client initialisieren
    api = LaravelAPIClient(
        base_url="https://your-laravel-api.com/api",
        api_token="your_api_token_here"  # Optional
    )
    
    try:
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
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Fehler: {e}")
    except Exception as e:
        print(f"Fehler: {e}")
