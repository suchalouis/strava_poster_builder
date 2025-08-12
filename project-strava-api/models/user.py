"""
Modèles utilisateur simples (en mémoire)
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class StravaTokens(BaseModel):
    """Tokens Strava pour un utilisateur"""
    access_token: str
    refresh_token: str
    expires_at: int
    scope: str = ""
    token_type: str = "Bearer"
    
    def is_expired(self) -> bool:
        """Vérifier si le token est expiré"""
        import time
        return time.time() >= (self.expires_at - 300)  # Buffer de 5 minutes


class User(BaseModel):
    """Modèle utilisateur simple"""
    id: int
    strava_id: int
    email: Optional[str] = None
    username: Optional[str] = None
    strava_username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    sex: Optional[str] = None
    
    # Status
    is_active: bool = True
    is_verified: bool = True
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    # Tokens Strava associés
    strava_tokens: Optional[StravaTokens] = None
    
    @property
    def full_name(self) -> str:
        """Nom complet de l'utilisateur"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.strava_username or self.username or "Anonymous"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire pour sérialisation"""
        return {
            "id": self.id,
            "strava_id": self.strava_id,
            "email": self.email,
            "username": self.username,
            "strava_username": self.strava_username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "profile_picture": self.profile_picture,
            "city": self.city,
            "country": self.country,
            "sex": self.sex,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
    
    class Config:
        # Permettre l'utilisation de datetime et autres types
        arbitrary_types_allowed = True