"""
Strava OAuth authentication manager
Handles OAuth flow, token management and refresh
"""

import secrets
import urllib.parse
import requests
from typing import Dict, List, Optional, Any, Callable
from .exceptions import StravaAuthException, StravaRateLimitException, StravaTokenExpiredException
from .models import StravaTokens


class StravaAuthManager:
    """Manager for Strava OAuth authentication flow"""
    
    STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
    STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token" 
    STRAVA_DEAUTHORIZE_URL = "https://www.strava.com/oauth/deauthorize"
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = None):
        """
        Initialize Strava OAuth manager
        
        Args:
            client_id: Strava application client ID
            client_secret: Strava application client secret  
            redirect_uri: OAuth redirect URI (optional)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri or "http://localhost:8000/auth/callback"
        
        # Optional callback for token updates
        self.token_update_callback: Optional[Callable[[StravaTokens], None]] = None
    
    def set_token_update_callback(self, callback: Callable[[StravaTokens], None]) -> None:
        """
        Set a callback function to be called when tokens are updated
        
        Args:
            callback: Function that receives StravaTokens when updated
        """
        self.token_update_callback = callback
    
    def build_auth_url(self, scope: List[str] = None, state: str = None) -> str:
        """
        Generate Strava OAuth authorization URL
        
        Args:
            scope: List of requested permissions
            state: CSRF protection state parameter
            
        Returns:
            Complete authorization URL
        """
        if scope is None:
            scope = ['read', 'activity:read_all', 'profile:read_all']
        
        if state is None:
            state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ','.join(scope),
            'approval_prompt': 'auto',
            'state': state
        }
        
        return f"{self.STRAVA_AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    def exchange_token(self, code: str) -> StravaTokens:
        """
        Exchange authorization code for access tokens
        
        Args:
            code: Authorization code received from OAuth callback
            
        Returns:
            StravaTokens object with access and refresh tokens
            
        Raises:
            StravaAuthException: If token exchange fails
        """
        try:
            response = requests.post(self.STRAVA_TOKEN_URL, data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code'
            })
            
            if response.status_code == 429:
                raise StravaRateLimitException(
                    "Rate limit exceeded during token exchange",
                    retry_after=response.headers.get('Retry-After')
                )
            
            if response.status_code != 200:
                raise StravaAuthException(
                    f"Token exchange failed: {response.text}",
                    status_code=response.status_code,
                    response_data=response.json() if response.content else None
                )
            
            token_data = response.json()
            tokens = StravaTokens.from_dict(token_data)
            
            # Call update callback if set
            if self.token_update_callback:
                self.token_update_callback(tokens)
            
            return tokens
            
        except requests.exceptions.RequestException as e:
            raise StravaAuthException(f"Network error during token exchange: {e}")
    
    def refresh_token(self, refresh_token: str) -> StravaTokens:
        """
        Refresh an expired access token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            StravaTokens object with new access and refresh tokens
            
        Raises:
            StravaTokenExpiredException: If refresh token is invalid
            StravaAuthException: If refresh fails
        """
        try:
            response = requests.post(self.STRAVA_TOKEN_URL, data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            })
            
            if response.status_code == 429:
                raise StravaRateLimitException(
                    "Rate limit exceeded during token refresh",
                    retry_after=response.headers.get('Retry-After')
                )
            
            if response.status_code == 401:
                raise StravaTokenExpiredException("Refresh token is invalid or expired")
            
            if response.status_code != 200:
                raise StravaAuthException(
                    f"Token refresh failed: {response.text}",
                    status_code=response.status_code,
                    response_data=response.json() if response.content else None
                )
            
            token_data = response.json()
            tokens = StravaTokens.from_dict(token_data)
            
            # Call update callback if set
            if self.token_update_callback:
                self.token_update_callback(tokens)
            
            return tokens
            
        except requests.exceptions.RequestException as e:
            raise StravaAuthException(f"Network error during token refresh: {e}")
    
    def revoke_token(self, access_token: str) -> bool:
        """
        Revoke/deauthorize an access token
        
        Args:
            access_token: Valid access token to revoke
            
        Returns:
            True if successfully revoked, False otherwise
        """
        try:
            response = requests.post(self.STRAVA_DEAUTHORIZE_URL, data={
                'access_token': access_token
            })
            
            return response.status_code == 200
            
        except requests.exceptions.RequestException:
            return False
    
    def validate_tokens(self, tokens: StravaTokens) -> bool:
        """
        Validate that tokens are properly formatted
        
        Args:
            tokens: StravaTokens to validate
            
        Returns:
            True if tokens are valid format, False otherwise
        """
        if not tokens.access_token or not tokens.refresh_token:
            return False
        
        if not tokens.expires_at or tokens.expires_at <= 0:
            return False
        
        return True
    
    @staticmethod
    def generate_state() -> str:
        """Generate a secure random state parameter for CSRF protection"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_scopes_description() -> Dict[str, str]:
        """Get description of available OAuth scopes"""
        return {
            'read': 'Read public profile information',
            'read_all': 'Read all profile information',
            'profile:read_all': 'Read all profile information including email',
            'profile:write': 'Update profile information',
            'activity:read': 'Read public activities',
            'activity:read_all': 'Read all activities including private',
            'activity:write': 'Create and update activities'
        }