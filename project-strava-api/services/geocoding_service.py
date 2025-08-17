"""
Service de géocodage inversé pour récupérer les noms de villes à partir de coordonnées GPS
Utilise l'API Nominatim d'OpenStreetMap (gratuite et sans clé API)
"""

import asyncio
import logging
from typing import Optional, List, Tuple
from urllib.parse import urlencode

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    import requests

logger = logging.getLogger(__name__)


class GeocodingService:
    """Service de géocodage inversé utilisant l'API Nominatim d'OpenStreetMap"""
    
    def __init__(self, timeout: int = 10):
        """
        Initialise le service de géocodage
        
        Args:
            timeout: Timeout en secondes pour les requêtes HTTP
        """
        self.base_url = "https://nominatim.openstreetmap.org/reverse"
        self.timeout = timeout
        self.user_agent = "Strava Poster Builder/1.0"
        
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Effectue un géocodage inversé pour obtenir le nom de la ville
        
        Args:
            latitude: Latitude du point
            longitude: Longitude du point
            
        Returns:
            Nom de la ville ou None si non trouvé
        """
        try:
            params = {
                'lat': str(latitude),
                'lon': str(longitude),
                'format': 'json',
                'addressdetails': 1,
                'accept-language': 'fr,en',  # Préférence pour le français
                'zoom': 10  # Niveau de zoom pour favoriser les villes
            }
            
            url = f"{self.base_url}?{urlencode(params)}"
            
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/json'
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._extract_city_name(data)
                    else:
                        logger.warning(f"Erreur géocodage: HTTP {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout géocodage pour {latitude}, {longitude}")
            return None
        except Exception as e:
            logger.error(f"Erreur géocodage pour {latitude}, {longitude}: {e}")
            return None
    
    def _extract_city_name(self, data: dict) -> Optional[str]:
        """
        Extrait le nom de la ville à partir de la réponse Nominatim
        
        Args:
            data: Réponse JSON de Nominatim
            
        Returns:
            Nom de la ville ou None
        """
        try:
            address = data.get('address', {})
            
            # Priorités pour le nom de la ville (du plus spécifique au plus général)
            city_keys = [
                'city',
                'town', 
                'village',
                'municipality',
                'suburb',
                'district',
                'county',
                'state_district',
                'state'
            ]
            
            for key in city_keys:
                if key in address and address[key]:
                    city_name = address[key].strip()
                    # Nettoyer les noms composés (garder seulement la première partie)
                    if ' - ' in city_name:
                        city_name = city_name.split(' - ')[0]
                    if city_name:
                        logger.debug(f"Ville trouvée: {city_name} (clé: {key})")
                        return city_name
            
            # Fallback sur le nom d'affichage simplifié
            display_name = data.get('display_name', '')
            if display_name:
                # Prendre la première partie du nom d'affichage
                parts = display_name.split(',')
                if len(parts) > 1:
                    potential_city = parts[0].strip()
                    if potential_city and not potential_city.isdigit():
                        logger.debug(f"Ville extraite du display_name: {potential_city}")
                        return potential_city
            
            logger.warning("Aucun nom de ville trouvé dans la réponse géocodage")
            return None
            
        except Exception as e:
            logger.error(f"Erreur extraction nom de ville: {e}")
            return None
    
    def reverse_geocode_sync(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Version synchrone du géocodage inversé
        
        Args:
            latitude: Latitude du point
            longitude: Longitude du point
            
        Returns:
            Nom de la ville ou None si non trouvé
        """
        if not AIOHTTP_AVAILABLE:
            # Utiliser requests en fallback
            return self._reverse_geocode_requests(latitude, longitude)
        
        try:
            # Créer une nouvelle boucle d'événements si nécessaire
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Si une boucle est déjà en cours, utiliser asyncio.create_task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run, 
                            self.reverse_geocode(latitude, longitude)
                        )
                        return future.result(timeout=self.timeout + 5)
                else:
                    return loop.run_until_complete(self.reverse_geocode(latitude, longitude))
            except RuntimeError:
                # Pas de boucle d'événements, en créer une nouvelle
                return asyncio.run(self.reverse_geocode(latitude, longitude))
                
        except Exception as e:
            logger.error(f"Erreur géocodage synchrone pour {latitude}, {longitude}: {e}")
            return None
    
    def _reverse_geocode_requests(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Version fallback utilisant requests au lieu d'aiohttp
        
        Args:
            latitude: Latitude du point
            longitude: Longitude du point
            
        Returns:
            Nom de la ville ou None si non trouvé
        """
        try:
            params = {
                'lat': str(latitude),
                'lon': str(longitude),
                'format': 'json',
                'addressdetails': 1,
                'accept-language': 'fr,en',  # Préférence pour le français
                'zoom': 10  # Niveau de zoom pour favoriser les villes
            }
            
            url = f"{self.base_url}?{urlencode(params)}"
            
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return self._extract_city_name(data)
            else:
                logger.warning(f"Erreur géocodage: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout géocodage pour {latitude}, {longitude}")
            return None
        except Exception as e:
            logger.error(f"Erreur géocodage requests pour {latitude}, {longitude}: {e}")
            return None
    
    def get_city_from_coordinates(self, start_latlng: List[float]) -> str:
        """
        Récupère le nom de la ville à partir des coordonnées de départ
        
        Args:
            start_latlng: Liste [latitude, longitude]
            
        Returns:
            Nom de la ville ou message de fallback
        """
        if not start_latlng or len(start_latlng) != 2:
            logger.warning("Coordonnées GPS manquantes ou invalides")
            return "Lieu inconnu"
        
        try:
            latitude, longitude = start_latlng
            
            # Validation des coordonnées
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                logger.warning(f"Coordonnées GPS invalides: {latitude}, {longitude}")
                return "Coordonnées invalides"
            
            # Tentative de géocodage
            city_name = self.reverse_geocode_sync(latitude, longitude)
            
            if city_name:
                return city_name
            else:
                # Fallback avec les coordonnées
                return f"Lat {latitude:.3f}, Lon {longitude:.3f}"
                
        except Exception as e:
            logger.error(f"Erreur récupération ville: {e}")
            return "Erreur géocodage"


# Instance globale pour réutilisation
_geocoding_service = None

def get_geocoding_service() -> GeocodingService:
    """
    Récupère l'instance globale du service de géocodage
    
    Returns:
        Instance du GeocodingService
    """
    global _geocoding_service
    if _geocoding_service is None:
        _geocoding_service = GeocodingService()
    return _geocoding_service