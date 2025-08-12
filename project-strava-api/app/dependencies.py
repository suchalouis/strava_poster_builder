"""
Dépendances communes FastAPI
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.user import User
from services.user_service import user_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)


async def get_current_user_from_session(
    request: Request,
    session_id: Optional[str] = Cookie(None, alias="strava_session")
) -> Optional[User]:
    """
    Récupère l'utilisateur actuel depuis la session (comme l'ancien système Flask)
    """
    try:
        # Chercher dans les headers d'abord (pour les sessions de développement)
        if hasattr(request, 'cookies') and request.cookies:
            for cookie_name, cookie_value in request.cookies.items():
                if cookie_name.startswith('session') or 'strava' in cookie_name.lower():
                    session_id = cookie_value
                    break
        
        if not session_id:
            return None
            
        # Récupérer l'utilisateur depuis la session
        user = await user_service.get_user_from_session(session_id)
        if user:
            logger.debug(f"Found user {user.id} from session {session_id[:10]}...")
        return user
        
    except Exception as e:
        logger.error(f"Error getting user from session: {e}")
        return None


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Récupère l'utilisateur actuel (session ou JWT)
    """
    # Essayer d'abord via la session (comme Flask)
    user = await get_current_user_from_session(request)
    if user:
        return user
    
    # Fallback vers JWT si pas de session
    if credentials:
        try:
            from core.security import decode_access_token
            payload = decode_access_token(credentials.credentials)
            user_id: str = payload.get("sub")
            if user_id:
                user = await user_service.get_user_by_id(int(user_id))
                if user:
                    return user
        except Exception as e:
            logger.debug(f"JWT auth failed: {e}")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated"
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Vérifie que l'utilisateur actuel est actif
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_user_service():
    """Dependency pour UserService"""
    return user_service


async def get_strava_service(
    current_user: User = Depends(get_current_active_user)
):
    """Dependency pour StravaService avec utilisateur authentifié"""
    from services.strava_service import StravaService
    return StravaService(current_user)


async def get_poster_service(
    current_user: User = Depends(get_current_active_user)
):
    """Dependency pour PosterService avec utilisateur authentifié"""
    from services.poster_service import PosterService
    return PosterService(current_user)