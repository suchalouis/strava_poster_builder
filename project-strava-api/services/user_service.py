"""
Service de gestion des utilisateurs (en mémoire)
"""

from typing import Optional, Dict, List
from datetime import datetime, timedelta
import secrets

from models.user import User, StravaTokens
from models.session import UserSession, OAuthState
from core.security import create_session_token
import logging

logger = logging.getLogger(__name__)


class InMemoryUserService:
    """Service utilisateur avec stockage en mémoire"""
    
    def __init__(self):
        # Stockage en mémoire
        self.users: Dict[int, User] = {}  # user_id -> User
        self.users_by_strava_id: Dict[int, int] = {}  # strava_id -> user_id
        self.sessions: Dict[str, UserSession] = {}  # session_token -> UserSession
        self.oauth_states: Dict[str, OAuthState] = {}  # state -> OAuthState
        self._next_user_id = 1
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Récupérer un utilisateur par son ID"""
        return self.users.get(user_id)
    
    async def get_user_by_strava_id(self, strava_id: int) -> Optional[User]:
        """Récupérer un utilisateur par son ID Strava"""
        user_id = self.users_by_strava_id.get(strava_id)
        if user_id:
            return self.users.get(user_id)
        return None
    
    async def create_user_from_strava(self, strava_data: dict) -> User:
        """Créer un utilisateur à partir des données Strava"""
        user_id = self._next_user_id
        self._next_user_id += 1
        
        user = User(
            id=user_id,
            strava_id=strava_data.get('id'),
            strava_username=strava_data.get('username'),
            first_name=strava_data.get('firstname'),
            last_name=strava_data.get('lastname'),
            email=strava_data.get('email'),
            profile_picture=strava_data.get('profile_medium'),
            city=strava_data.get('city'),
            country=strava_data.get('country'),
            sex=strava_data.get('sex'),
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        
        # Stocker l'utilisateur
        self.users[user_id] = user
        self.users_by_strava_id[strava_data.get('id')] = user_id
        
        logger.info(f"Created user from Strava: {user.id} (Strava ID: {user.strava_id})")
        return user
    
    async def update_user(self, user_id: int, update_data: dict) -> Optional[User]:
        """Mettre à jour un utilisateur"""
        user = self.users.get(user_id)
        if not user:
            return None
        
        # Créer un nouvel objet User avec les données mises à jour
        user_dict = user.dict()
        user_dict.update(update_data)
        user_dict['updated_at'] = datetime.utcnow()
        
        updated_user = User(**user_dict)
        self.users[user_id] = updated_user
        
        logger.info(f"Updated user: {user_id}")
        return updated_user
    
    async def update_last_login(self, user_id: int) -> None:
        """Mettre à jour la dernière connexion"""
        user = self.users.get(user_id)
        if user:
            user_dict = user.dict()
            user_dict['last_login'] = datetime.utcnow()
            self.users[user_id] = User(**user_dict)
    
    async def store_strava_tokens(self, user_id: int, tokens_data: dict) -> bool:
        """Stocker les tokens Strava pour un utilisateur"""
        user = self.users.get(user_id)
        if not user:
            return False
        
        strava_tokens = StravaTokens(
            access_token=tokens_data['access_token'],
            refresh_token=tokens_data['refresh_token'],
            expires_at=tokens_data['expires_at'],
            scope=tokens_data.get('scope', ''),
            token_type=tokens_data.get('token_type', 'Bearer')
        )
        
        # Mettre à jour l'utilisateur avec les nouveaux tokens
        user_dict = user.dict()
        user_dict['strava_tokens'] = strava_tokens
        self.users[user_id] = User(**user_dict)
        
        logger.info(f"Stored Strava tokens for user: {user_id}")
        return True
    
    async def get_strava_tokens(self, user_id: int) -> Optional[StravaTokens]:
        """Récupérer les tokens Strava d'un utilisateur"""
        user = self.users.get(user_id)
        return user.strava_tokens if user else None
    
    async def create_user_session(self, user_id: int, user_agent: str = None, ip_address: str = None) -> UserSession:
        """Créer une session utilisateur"""
        session_token = create_session_token()
        
        session = UserSession(
            session_id=session_token,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(days=7),
            user_agent=user_agent[:500] if user_agent else None,
            ip_address=ip_address,
            is_active=True,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        self.sessions[session_token] = session
        
        logger.info(f"Created session for user: {user_id}")
        return session
    
    async def get_session(self, session_token: str) -> Optional[UserSession]:
        """Récupérer une session par token"""
        session = self.sessions.get(session_token)
        if session and not session.is_expired():
            return session
        elif session and session.is_expired():
            # Supprimer la session expirée
            del self.sessions[session_token]
        return None
    
    async def revoke_session(self, session_token: str) -> bool:
        """Révoquer une session"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False
    
    async def get_user_from_session(self, session_token: str) -> Optional[User]:
        """Récupérer un utilisateur depuis un token de session"""
        session = await self.get_session(session_token)
        if session:
            return await self.get_user_by_id(session.user_id)
        return None
    
    async def get_session_for_user(self, user_id: int) -> Optional[UserSession]:
        """Récupérer la session active la plus récente pour un utilisateur"""
        for session in self.sessions.values():
            if session.user_id == user_id and not session.is_expired():
                return session
        return None
    
    async def create_oauth_state(self, ip_address: str = None, user_agent: str = None) -> OAuthState:
        """Créer un état OAuth pour CSRF protection"""
        state = OAuthState(
            state=secrets.token_urlsafe(32),
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            is_used=False,
            created_at=datetime.utcnow()
        )
        
        self.oauth_states[state.state] = state
        return state
    
    async def verify_oauth_state(self, state_value: str) -> bool:
        """Vérifier et consommer un état OAuth"""
        oauth_state = self.oauth_states.get(state_value)
        if not oauth_state or oauth_state.is_used or oauth_state.is_expired():
            return False
        
        # Marquer comme utilisé
        oauth_state.is_used = True
        return True
    
    async def cleanup_expired_data(self) -> dict:
        """Nettoyer les données expirées"""
        now = datetime.utcnow()
        
        # Sessions expirées
        expired_sessions = [
            token for token, session in self.sessions.items()
            if session.expires_at < now
        ]
        for token in expired_sessions:
            del self.sessions[token]
        
        # États OAuth expirés
        expired_states = [
            state for state, oauth in self.oauth_states.items()
            if oauth.expires_at < now
        ]
        for state in expired_states:
            del self.oauth_states[state]
        
        cleanup_stats = {
            "expired_sessions": len(expired_sessions),
            "expired_oauth_states": len(expired_states)
        }
        
        logger.info(f"Cleanup completed: {cleanup_stats}")
        return cleanup_stats


# Instance globale
user_service = InMemoryUserService()