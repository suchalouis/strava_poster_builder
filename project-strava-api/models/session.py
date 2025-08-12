"""
Modèles de session simples (en mémoire)
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class UserSession(BaseModel):
    """Session utilisateur en mémoire"""
    session_id: str
    user_id: int
    expires_at: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    last_activity: datetime
    
    def is_expired(self) -> bool:
        """Vérifier si la session est expirée"""
        return datetime.utcnow() >= self.expires_at
    
    class Config:
        arbitrary_types_allowed = True


class OAuthState(BaseModel):
    """État OAuth pour protection CSRF"""
    state: str
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_used: bool = False
    created_at: datetime
    
    def is_expired(self) -> bool:
        """Vérifier si l'état OAuth est expiré"""
        return datetime.utcnow() >= self.expires_at
    
    class Config:
        arbitrary_types_allowed = True