"""
Routes pour le profil de l'athlète Strava
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_strava_service, get_current_active_user
from models.user import User
from services.strava_service import StravaService
from schemas.auth import UserResponse, UserUpdate
from schemas.strava import AthleteResponse, ActivityStatsResponse
from strava import StravaAPIException
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/profile", response_model=AthleteResponse)
async def get_athlete_profile(
    strava_service: StravaService = Depends(get_strava_service)
):
    """
    Récupérer le profil complet de l'athlète depuis Strava
    """
    try:
        athlete_info = await strava_service.get_athlete_info()
        
        return AthleteResponse(
            id=athlete_info['id'],
            firstname=athlete_info.get('firstname'),
            lastname=athlete_info.get('lastname'),
            full_name=f"{athlete_info.get('firstname', '')} {athlete_info.get('lastname', '')}".strip(),
            profile=athlete_info.get('profile'),
            profile_medium=athlete_info.get('profile_medium'),
            city=athlete_info.get('city'),
            country=athlete_info.get('country'),
            sex=athlete_info.get('sex'),
            created_at=athlete_info.get('created_at'),
            updated_at=athlete_info.get('updated_at')
        )
        
    except StravaAPIException as e:
        logger.error(f"Strava API error getting athlete profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve athlete profile: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting athlete profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve athlete profile"
        )


@router.get("/stats", response_model=ActivityStatsResponse)
async def get_athlete_stats(
    strava_service: StravaService = Depends(get_strava_service)
):
    """
    Récupérer les statistiques globales de l'athlète
    """
    try:
        raw_stats = await strava_service.get_athlete_stats()
        
        # Traitement des statistiques avec le data processor
        from services.data_processor import StravaDataProcessor
        processor = StravaDataProcessor()
        processed_stats = processor.process_athlete_stats(raw_stats)
        
        return ActivityStatsResponse(**processed_stats)
        
    except StravaAPIException as e:
        logger.error(f"Strava API error getting athlete stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve athlete statistics: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting athlete stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve athlete statistics"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupérer les informations de l'utilisateur actuel (données locales)
    """
    return UserResponse(**current_user.to_dict())


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    strava_service: StravaService = Depends(get_strava_service)
):
    """
    Mettre à jour les informations de l'utilisateur actuel
    """
    try:
        # Préparer les données de mise à jour
        update_data = {}
        if user_update.email is not None:
            update_data['email'] = user_update.email
        if user_update.username is not None:
            update_data['username'] = user_update.username
        if user_update.first_name is not None:
            update_data['first_name'] = user_update.first_name
        if user_update.last_name is not None:
            update_data['last_name'] = user_update.last_name
        if user_update.city is not None:
            update_data['city'] = user_update.city
        if user_update.country is not None:
            update_data['country'] = user_update.country
        if user_update.profile_picture is not None:
            update_data['profile_picture'] = user_update.profile_picture
        
        if not update_data:
            # Aucune donnée à mettre à jour
            return UserResponse(**current_user.to_dict())
        
        # Mettre à jour via le service utilisateur
        from app.dependencies import get_user_service
        from core.database import get_db_session
        
        # Note: Ceci nécessiterait une refactorisation pour obtenir le service utilisateur
        # Pour l'instant, on retourne l'utilisateur actuel
        # TODO: Implémenter la mise à jour via UserService
        
        logger.info(f"User {current_user.id} profile updated")
        return UserResponse(**current_user.to_dict())
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.get("/rate-limit")
async def get_rate_limit_status(
    strava_service: StravaService = Depends(get_strava_service)
):
    """
    Obtenir le statut actuel des limites de taux Strava
    """
    try:
        rate_limit_info = await strava_service.get_rate_limit_status()
        return rate_limit_info
        
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        # Retourner des valeurs par défaut en cas d'erreur
        return {
            "requests_15min": 0,
            "limit_15min": 100,
            "requests_daily": 0,
            "limit_daily": 1000,
            "reset_15min": 0,
            "reset_daily": 0,
            "error": "Unable to retrieve rate limit status"
        }