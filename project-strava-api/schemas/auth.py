"""
Schémas Pydantic pour l'authentification
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Schéma de base utilisateur"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    """Schéma pour la création d'un utilisateur"""
    strava_id: int
    strava_username: Optional[str] = None


class UserUpdate(BaseModel):
    """Schéma pour la mise à jour d'un utilisateur"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    profile_picture: Optional[str] = None


class UserResponse(UserBase):
    """Schéma de réponse utilisateur"""
    id: int
    strava_id: Optional[int] = None
    strava_username: Optional[str] = None
    full_name: str
    profile_picture: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    sex: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Schéma de réponse pour les tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    """Schéma pour le rafraîchissement de token"""
    refresh_token: str


class LoginResponse(BaseModel):
    """Schéma de réponse de connexion"""
    user: UserResponse
    tokens: TokenResponse


class OAuthCallback(BaseModel):
    """Schéma pour le callback OAuth"""
    code: str
    state: str
    scope: Optional[str] = None


class StravaTokens(BaseModel):
    """Schéma pour les tokens Strava"""
    access_token: str
    refresh_token: str
    expires_at: int
    scope: str