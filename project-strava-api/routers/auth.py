"""
Routes d'authentification OAuth Strava
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from typing import Dict, Any

from app.dependencies import get_user_service, get_current_active_user
from core.security import TokenManager
from schemas.auth import LoginResponse, OAuthCallback, TokenRefresh, TokenResponse, UserResponse
from services.user_service import user_service
from strava import StravaAuthManager, StravaAPIException
from app.config import settings
from models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/login")
async def initiate_oauth_login(
    request: Request
):
    """
    Initier le processus de connexion OAuth avec Strava
    """
    try:
        # Créer un état OAuth pour CSRF protection
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent")
        
        oauth_state = await user_service.create_oauth_state(
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Générer l'URL d'autorisation Strava
        auth_manager = StravaAuthManager(
            client_id=settings.strava_client_id,
            client_secret=settings.strava_client_secret,
            redirect_uri=settings.strava_redirect_uri
        )
        
        auth_url = auth_manager.build_auth_url(
            scope=['read', 'activity:read_all', 'profile:read_all'],
            state=oauth_state.state
        )
        
        logger.info(f"OAuth login initiated from IP {client_ip}")
        
        return {
            "auth_url": auth_url,
            "state": oauth_state.state
        }
        
    except Exception as e:
        logger.error(f"Error initiating OAuth login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth login"
        )


@router.get("/callback", response_class=HTMLResponse)
async def oauth_callback(
    code: str,
    state: str,
    request: Request,
    scope: str = None
):
    """
    Gérer le callback OAuth de Strava
    """
    try:
        # Vérifier l'état OAuth
        if not await user_service.verify_oauth_state(state):
            logger.warning(f"Invalid OAuth state: {state}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OAuth state"
            )
        
        # Échanger le code contre des tokens
        auth_manager = StravaAuthManager(
            client_id=settings.strava_client_id,
            client_secret=settings.strava_client_secret
        )
        
        strava_tokens = auth_manager.exchange_token(code)
        
        # Récupérer les données athlète depuis Strava
        from strava import StravaClient
        temp_client = StravaClient(
            client_id=settings.strava_client_id,
            client_secret=settings.strava_client_secret
        )
        temp_client.set_access_token(
            access_token=strava_tokens.access_token,
            refresh_token=strava_tokens.refresh_token,
            expires_at=strava_tokens.expires_at
        )
        
        athlete_data = temp_client.get_athlete()
        
        # Rechercher ou créer l'utilisateur
        user = await user_service.get_user_by_strava_id(athlete_data['id'])
        if not user:
            user = await user_service.create_user_from_strava(athlete_data)
        else:
            # Mettre à jour la dernière connexion
            await user_service.update_last_login(user.id)
        
        # Stocker les tokens Strava
        await user_service.store_strava_tokens(user.id, {
            'access_token': strava_tokens.access_token,
            'refresh_token': strava_tokens.refresh_token,
            'expires_at': strava_tokens.expires_at,
            'scope': strava_tokens.scope
        })
        
        # Créer les tokens JWT pour l'application
        app_tokens = TokenManager.create_user_tokens(user.id)
        
        # Créer une session utilisateur
        client_ip = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        await user_service.create_user_session(
            user_id=user.id,
            user_agent=user_agent,
            ip_address=client_ip
        )
        
        logger.info(f"Successful OAuth login for user {user.id} (Strava ID: {athlete_data['id']})")
        
        # Créer la réponse HTML avec le cookie de session
        html_content = """
        <html>
        <head>
            <title>Authentification réussie</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 2rem;
                    background: linear-gradient(135deg, #fc4c02, #ff6b35);
                    color: white;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .success { 
                    background: rgba(255,255,255,0.1);
                    padding: 2rem;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                .checkmark {
                    font-size: 4rem;
                    margin-bottom: 1rem;
                }
            </style>
        </head>
        <body>
            <div class="success">
                <div class="checkmark">✅</div>
                <h1>Authentification réussie !</h1>
                <p>Cette fenêtre va se fermer automatiquement...</p>
            </div>
            
            <script>
                // Envoyer un message au parent pour indiquer le succès
                try {
                    if (window.opener) {
                        window.opener.postMessage({
                            type: 'strava_auth_success',
                            success: true
                        }, window.location.origin);
                        window.close();
                    } else {
                        // Fallback si pas de popup parent
                        setTimeout(() => {
                            window.location.href = '/home';
                        }, 2000);
                    }
                } catch (error) {
                    console.error('Error communicating with parent:', error);
                    // Fallback redirection
                    setTimeout(() => {
                        window.location.href = '/home';
                    }, 2000);
                }
            </script>
        </body>
        </html>
        """
        
        # Créer la réponse avec le cookie de session
        response = HTMLResponse(content=html_content)
        
        # Récupérer la session créée
        session = await user_service.get_session_for_user(user.id)
        if session:
            # Définir le cookie de session (comme Flask)
            response.set_cookie(
                key="strava_session",
                value=session.session_id,
                max_age=86400,  # 24 heures
                httponly=True,
                secure=False,  # True en production avec HTTPS
                samesite="lax"
            )
        
        return response
        
    except StravaAPIException as e:
        logger.error(f"Strava API error during callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Strava authentication failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing OAuth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_auth(
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupérer les informations de l'utilisateur actuel (route auth)
    """
    return UserResponse(**current_user.to_dict())


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    token_refresh: TokenRefresh
):
    """
    Rafraîchir un token d'accès expiré
    """
    try:
        # Décoder le refresh token
        payload = TokenManager.decode_refresh_token(token_refresh.refresh_token)
        user_id = int(payload["sub"])
        
        # Vérifier que l'utilisateur existe
        user = await user_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Créer de nouveaux tokens
        new_tokens = TokenManager.create_user_tokens(user_id)
        
        logger.info(f"Token refreshed for user {user_id}")
        
        return TokenResponse(
            access_token=new_tokens["access_token"],
            refresh_token=new_tokens["refresh_token"],
            token_type=new_tokens["token_type"],
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user = Depends()  # TODO: Add proper current user dependency
):
    """
    Déconnecter l'utilisateur et révoquer les sessions
    """
    try:
        # Révoquer toutes les sessions actives de l'utilisateur
        # TODO: Implémenter la révocation des sessions
        
        logger.info(f"User {current_user.id} logged out")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/status")
async def auth_status(
    current_user = Depends()  # TODO: Add proper current user dependency
):
    """
    Vérifier le statut d'authentification
    """
    return {
        "authenticated": True,
        "user_id": current_user.id,
        "strava_id": current_user.strava_id
    }