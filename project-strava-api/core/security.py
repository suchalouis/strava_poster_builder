"""
Sécurité : JWT, hachage des mots de passe, etc.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from jose import jwt
from passlib.context import CryptContext

from app.config import settings

# Context pour le hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Créer un token JWT d'accès
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Décoder un token JWT
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifier un mot de passe
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hasher un mot de passe
    """
    return pwd_context.hash(password)


def create_session_token() -> str:
    """
    Créer un token de session sécurisé
    """
    import secrets
    return secrets.token_urlsafe(32)


class TokenManager:
    """
    Gestionnaire de tokens pour les utilisateurs
    """
    
    @staticmethod
    def create_user_tokens(user_id: int, additional_claims: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Créer les tokens d'accès et de rafraîchissement pour un utilisateur
        """
        claims = {"sub": str(user_id), "type": "access"}
        if additional_claims:
            claims.update(additional_claims)
        
        access_token = create_access_token(claims)
        
        # Token de rafraîchissement (durée plus longue)
        refresh_claims = {"sub": str(user_id), "type": "refresh"}
        refresh_token = create_access_token(
            refresh_claims, 
            expires_delta=timedelta(days=7)
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def decode_refresh_token(token: str) -> Dict[str, Any]:
        """
        Décoder un token de rafraîchissement
        """
        payload = decode_access_token(token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        return payload