"""
Service d'orchestration pour l'API Strava
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from strava import StravaClient, StravaAPIException, StravaTokenExpiredException
from models.user import User, StravaTokens
from services.user_service import user_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class StravaService:
    """Service pour orchestrer les interactions avec l'API Strava"""
    
    def __init__(self, user: User):
        self.user = user
        self._client: Optional[StravaClient] = None
    
    async def _get_strava_client(self) -> StravaClient:
        """
        Obtenir un client Strava configuré avec les tokens de l'utilisateur
        """
        if self._client is None:
            # Récupérer les tokens Strava de l'utilisateur
            strava_tokens = await user_service.get_strava_tokens(self.user.id)
            if not strava_tokens:
                raise StravaAPIException("No Strava tokens found for user")
            
            # Initialiser le client
            self._client = StravaClient(
                client_id=settings.strava_client_id,
                client_secret=settings.strava_client_secret,
                redirect_uri=settings.strava_redirect_uri
            )
            
            # Configurer les tokens
            self._client.set_access_token(
                access_token=strava_tokens.access_token,
                refresh_token=strava_tokens.refresh_token,
                expires_at=strava_tokens.expires_at
            )
            
            # Callback pour la mise à jour des tokens
            self._client.set_token_update_callback(self._on_token_updated)
        
        return self._client
    
    async def _on_token_updated(self, tokens) -> None:
        """
        Callback appelé quand les tokens sont mis à jour (refresh automatique)
        """
        try:
            await user_service.store_strava_tokens(self.user.id, {
                'access_token': tokens.access_token,
                'refresh_token': tokens.refresh_token,
                'expires_at': tokens.expires_at,
                'scope': tokens.scope
            })
            logger.info(f"Updated Strava tokens for user {self.user.id}")
        except Exception as e:
            logger.error(f"Failed to update tokens for user {self.user.id}: {e}")
    
    async def get_athlete_info(self) -> Dict[str, Any]:
        """Récupérer les informations de l'athlète"""
        try:
            client = await self._get_strava_client()
            athlete_data = client.get_athlete()
            
            # Mettre à jour les informations utilisateur si nécessaire
            if self.user.strava_id == athlete_data.get('id'):
                await self._update_user_from_athlete_data(athlete_data)
            
            return athlete_data
        except Exception as e:
            logger.error(f"Error getting athlete info for user {self.user.id}: {e}")
            raise
    
    async def get_athlete_stats(self) -> Dict[str, Any]:
        """Récupérer les statistiques de l'athlète"""
        try:
            client = await self._get_strava_client()
            return client.get_athlete_stats()
        except Exception as e:
            logger.error(f"Error getting athlete stats for user {self.user.id}: {e}")
            raise
    
    async def get_activities(
        self, 
        before: Optional[int] = None,
        after: Optional[int] = None,
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """Récupérer les activités avec pagination"""
        try:
            client = await self._get_strava_client()
            activities = client.get_athlete_activities(
                before=before,
                after=after,
                page=page,
                per_page=per_page
            )
            
            # Enrichir avec les données de formatage
            formatted_activities = []
            for activity in activities:
                formatted_activity = self._format_activity_for_api(activity)
                formatted_activities.append(formatted_activity)
            
            return formatted_activities
        except Exception as e:
            logger.error(f"Error getting activities for user {self.user.id}: {e}")
            raise
    
    async def get_activities_by_year(self, year: int) -> List[Dict[str, Any]]:
        """Récupérer toutes les activités d'une année"""
        try:
            client = await self._get_strava_client()
            activities = client.get_activities_by_year(year)
            return [self._format_activity_for_api(activity) for activity in activities]
        except Exception as e:
            logger.error(f"Error getting activities for year {year} for user {self.user.id}: {e}")
            raise
    
    async def get_activities_by_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Récupérer les activités d'un mois"""
        try:
            client = await self._get_strava_client()
            activities = client.get_activities_by_month(year, month)
            return [self._format_activity_for_api(activity) for activity in activities]
        except Exception as e:
            logger.error(f"Error getting activities for {year}/{month} for user {self.user.id}: {e}")
            raise
    
    async def get_activity_detail(self, activity_id: int) -> Dict[str, Any]:
        """Récupérer les détails complets d'une activité"""
        try:
            client = await self._get_strava_client()
            return client.get_activity_full_details(activity_id)
        except Exception as e:
            logger.error(f"Error getting activity {activity_id} for user {self.user.id}: {e}")
            raise
    
    async def get_activity_gpx_data(self, activity_id: int) -> Optional[List[List[float]]]:
        """Récupérer les données GPS d'une activité"""
        try:
            client = await self._get_strava_client()
            return client.get_activity_gpx_data(activity_id)
        except Exception as e:
            logger.error(f"Error getting GPX for activity {activity_id} for user {self.user.id}: {e}")
            return None
    
    async def get_multiple_activities_gpx(self, activity_ids: List[int]) -> List[Dict[str, Any]]:
        """Récupérer les données GPS de plusieurs activités"""
        activities_gpx = []
        client = await self._get_strava_client()
        
        for activity_id in activity_ids:
            try:
                gpx_data = client.get_activity_gpx_data(activity_id)
                if gpx_data and len(gpx_data) > 0:
                    activities_gpx.append({
                        'activity_id': activity_id,
                        'coordinates': gpx_data,
                        'total_points': len(gpx_data)
                    })
            except Exception as e:
                logger.warning(f"Failed to get GPX for activity {activity_id}: {e}")
                continue
        
        return activities_gpx
    
    async def get_activities_summary(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        max_activities: Optional[int] = None
    ) -> Dict[str, Any]:
        """Récupérer un résumé complet des activités avec statistiques"""
        try:
            client = await self._get_strava_client()
            
            # Récupérer les activités selon les paramètres
            if year and month:
                activities = client.get_activities_by_month(year, month)
            elif year:
                activities = client.get_activities_by_year(year)
            else:
                activities = client.get_all_activities(max_activities=max_activities)
            
            # Traiter avec le data processor
            from services.data_processor import StravaDataProcessor
            processor = StravaDataProcessor()
            
            summary = processor.process_activities_summary(activities)
            
            # Ajouter des statistiques supplémentaires
            if len(activities) > 0:
                summary['monthly_stats'] = processor.get_monthly_stats(activities)
                summary['weekly_stats'] = processor.get_weekly_stats(activities)
                summary['personal_records'] = processor.get_personal_records(activities)
            
            return summary
        except Exception as e:
            logger.error(f"Error getting activities summary for user {self.user.id}: {e}")
            raise
    
    def _format_activity_for_api(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Formater une activité pour l'API en utilisant le data processor"""
        from services.data_processor import StravaDataProcessor
        processor = StravaDataProcessor()
        
        return {
            'id': activity.get('id'),
            'name': activity.get('name'),
            'type': activity.get('type'),
            'icon': processor.get_activity_icon(activity.get('type', '')),
            # Données formatées pour l'affichage
            'distance': processor.format_distance(activity.get('distance', 0)),
            'time': processor.format_time(activity.get('moving_time', 0)),
            'elevation': processor.format_elevation(activity.get('total_elevation_gain', 0)),
            # Données brutes pour les calculs
            'distance_raw': activity.get('distance', 0),
            'moving_time': activity.get('moving_time', 0),
            'total_elevation_gain': activity.get('total_elevation_gain', 0),
            'date': activity.get('start_date_local'),
            'formatted_date': processor.format_date(activity.get('start_date_local'))
        }
    
    async def _update_user_from_athlete_data(self, athlete_data: Dict[str, Any]) -> None:
        """Mettre à jour les informations utilisateur depuis les données athlète"""
        update_data = {}
        
        if athlete_data.get('firstname') and athlete_data['firstname'] != self.user.first_name:
            update_data['first_name'] = athlete_data['firstname']
        
        if athlete_data.get('lastname') and athlete_data['lastname'] != self.user.last_name:
            update_data['last_name'] = athlete_data['lastname']
        
        if athlete_data.get('profile_medium') and athlete_data['profile_medium'] != self.user.profile_picture:
            update_data['profile_picture'] = athlete_data['profile_medium']
        
        if athlete_data.get('city') and athlete_data['city'] != self.user.city:
            update_data['city'] = athlete_data['city']
        
        if athlete_data.get('country') and athlete_data['country'] != self.user.country:
            update_data['country'] = athlete_data['country']
        
        if update_data:
            await user_service.update_user(self.user.id, update_data)
            logger.info(f"Updated user {self.user.id} from athlete data")
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """Obtenir le statut des limites de taux"""
        try:
            client = await self._get_strava_client()
            return client.get_rate_limit_status()
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {
                "requests_15min": 0,
                "limit_15min": 100,
                "requests_daily": 0,
                "limit_daily": 1000,
                "error": str(e)
            }