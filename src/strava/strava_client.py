"""
Client Python pour l'API Strava
Gère la récupération et le cache des données Strava
"""

import requests
import time
from typing import Dict, List, Optional
import os
from datetime import datetime


class StravaClient:
    """Client pour interagir avec l'API Strava"""
    
    def __init__(self):
        self.base_url = "https://www.strava.com/api/v3"
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.expires_at: Optional[int] = None
        self.athlete_data: Optional[Dict] = None
        
        # Configuration OAuth depuis les variables d'environnement
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
        
    def set_tokens(self, access_token: str, refresh_token: str, expires_at: int, athlete: Dict = None):
        """Définir les tokens d'authentification"""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        self.athlete_data = athlete
        
    def _ensure_valid_token(self) -> str:
        """S'assurer que le token d'accès est valide, le rafraîchir si nécessaire"""
        if not self.access_token:
            raise ValueError("Aucun token d'accès disponible")
            
        # Vérifier si le token expire dans les 5 prochaines minutes
        if self.expires_at and time.time() >= (self.expires_at - 300):
            self._refresh_access_token()
            
        return self.access_token
    
    def _refresh_access_token(self):
        """Rafraîchir le token d'accès"""
        if not self.refresh_token:
            raise ValueError("Aucun refresh token disponible")
            
        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Erreur lors du rafraîchissement du token: {response.text}")
            
        data = response.json()
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']
        self.expires_at = data['expires_at']
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Effectuer une requête à l'API Strava"""
        token = self._ensure_valid_token()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=headers, params=params or {})
        
        if response.status_code == 401:
            # Token expiré, essayer de le rafraîchir
            self._refresh_access_token()
            headers['Authorization'] = f'Bearer {self.access_token}'
            response = requests.get(url, headers=headers, params=params or {})
            
        if response.status_code != 200:
            raise Exception(f"Erreur API Strava: {response.status_code} - {response.text}")
            
        return response.json()
    
    def get_athlete(self) -> Dict:
        """Récupérer les informations de l'athlète connecté"""
        return self._make_request("/athlete")
    
    def get_athlete_stats(self) -> Dict:
        """Récupérer les statistiques de l'athlète"""
        if not self.athlete_data or 'id' not in self.athlete_data:
            athlete = self.get_athlete()
            athlete_id = athlete['id']
        else:
            athlete_id = self.athlete_data['id']
            
        return self._make_request(f"/athletes/{athlete_id}/stats")
    
    def get_activities(self, per_page: int = 30, page: int = 1, after: int = None, before: int = None) -> List[Dict]:
        """
        Récupérer les activités de l'athlète
        
        Args:
            per_page: Nombre d'activités par page (max 200)
            page: Numéro de la page
            after: Timestamp Unix - récupérer les activités après cette date
            before: Timestamp Unix - récupérer les activités avant cette date
        """
        params = {
            'per_page': min(per_page, 200),
            'page': page
        }
        
        if after:
            params['after'] = after
        if before:
            params['before'] = before
            
        return self._make_request("/athlete/activities", params)
    
    def get_activity_details(self, activity_id: int) -> Dict:
        """Récupérer les détails complets d'une activité"""
        return self._make_request(f"/activities/{activity_id}")
    
    def get_all_activities(self, after: int = None, before: int = None, max_activities: int = None) -> List[Dict]:
        """
        Récupérer toutes les activités de l'athlète (pagination automatique)
        
        Args:
            after: Timestamp Unix - récupérer les activités après cette date
            before: Timestamp Unix - récupérer les activités avant cette date
            max_activities: Nombre maximum d'activités à récupérer
        """
        all_activities = []
        page = 1
        per_page = 200  # Maximum autorisé par l'API
        
        while True:
            activities = self.get_activities(
                per_page=per_page, 
                page=page, 
                after=after, 
                before=before
            )
            
            if not activities:
                break
                
            all_activities.extend(activities)
            
            # Vérifier si on a atteint le maximum demandé
            if max_activities and len(all_activities) >= max_activities:
                all_activities = all_activities[:max_activities]
                break
            
            # Si on a reçu moins que per_page, c'est la dernière page
            if len(activities) < per_page:
                break
                
            page += 1
            
            # Respect des limites de taux (100 requêtes par 15 min, 1000 par jour)
            time.sleep(0.1)
        
        return all_activities
    
    def get_activities_by_year(self, year: int) -> List[Dict]:
        """Récupérer toutes les activités d'une année donnée"""
        start_of_year = datetime(year, 1, 1)
        end_of_year = datetime(year + 1, 1, 1)
        
        after = int(start_of_year.timestamp())
        before = int(end_of_year.timestamp())
        
        return self.get_all_activities(after=after, before=before)
    
    def get_activities_by_month(self, year: int, month: int) -> List[Dict]:
        """Récupérer toutes les activités d'un mois donné"""
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
            
        start_of_month = datetime(year, month, 1)
        
        after = int(start_of_month.timestamp())
        before = int(next_month.timestamp())
        
        return self.get_all_activities(after=after, before=before)
    
    def get_recent_activities(self, count: int = 10) -> List[Dict]:
        """Récupérer les activités récentes"""
        return self.get_activities(per_page=count, page=1)