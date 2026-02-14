import requests
from typing import Optional, Dict, Any
import json


class LaravelAPIClient:
    """Client für die Kommunikation mit einer Laravel API"""
    
    def __init__(self, base_url: str, api_token: Optional[str] = None):
        """
        Initialisiert den API Client
        
        Args:
            base_url: Die Basis-URL der Laravel API (z.B. 'https://api.example.com')
            api_token: Optional - Bearer Token für Authentifizierung
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Standard Headers setzen
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        if api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {api_token}'
            })
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        GET Request an die API
        
        Args:
            endpoint: API Endpoint (z.B. '/users' oder '/posts/1')
            params: Optional - Query Parameter
            
        Returns:
            JSON Response als Dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST Request an die API
        
        Args:
            endpoint: API Endpoint
            data: Daten die gesendet werden sollen
            
        Returns:
            JSON Response als Dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        PUT Request an die API
        
        Args:
            endpoint: API Endpoint
            data: Daten die aktualisiert werden sollen
            
        Returns:
            JSON Response als Dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        DELETE Request an die API
        
        Args:
            endpoint: API Endpoint
            
        Returns:
            JSON Response als Dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url)
        response.raise_for_status()
        return response.json()


# Beispiel Verwendung
if __name__ == "__main__":
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
