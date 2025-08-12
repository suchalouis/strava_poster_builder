"""
Unified Strava API client
Handles OAuth authentication, API requests, and data parsing
"""

import time
import requests
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from .auth import StravaAuthManager
from .exceptions import (
    StravaAPIException, 
    StravaAuthException, 
    StravaRateLimitException,
    StravaTokenExpiredException,
    StravaDataNotFoundException,
    StravaNetworkException
)
from .models import StravaTokens, StravaAthlete, StravaActivity, StravaActivityStats, StravaStream


class StravaClient:
    """
    Unified Strava API client with OAuth authentication, API requests, and data parsing
    """
    
    API_BASE_URL = "https://www.strava.com/api/v3"
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = None):
        """
        Initialize Strava client
        
        Args:
            client_id: Strava application client ID
            client_secret: Strava application client secret
            redirect_uri: OAuth redirect URI (optional)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        
        # Authentication manager
        self.auth_manager = StravaAuthManager(client_id, client_secret, redirect_uri)
        
        # Current tokens
        self.tokens: Optional[StravaTokens] = None
        
        # Rate limiting state
        self._rate_limit_15min = {'count': 0, 'reset_time': time.time() + 900}
        self._rate_limit_daily = {'count': 0, 'reset_time': time.time() + 86400}
        
        # Optional callback for token updates
        self.token_update_callback: Optional[Callable[[StravaTokens], None]] = None
        
        # Set up auth manager callback
        self.auth_manager.set_token_update_callback(self._on_tokens_updated)
    
    def set_token_update_callback(self, callback: Callable[[StravaTokens], None]) -> None:
        """
        Set callback function to be called when tokens are updated
        
        Args:
            callback: Function that receives StravaTokens when updated
        """
        self.token_update_callback = callback
    
    def _on_tokens_updated(self, tokens: StravaTokens) -> None:
        """Internal callback when tokens are updated"""
        self.tokens = tokens
        if self.token_update_callback:
            self.token_update_callback(tokens)
    
    # === OAuth Authentication Methods ===
    
    def get_authorization_url(self, scope: List[str] = None) -> str:
        """
        Generate OAuth authorization URL
        
        Args:
            scope: List of requested permissions (read, read_all, profile:read_all, activity:read, activity:read_all)
            
        Returns:
            Complete authorization URL for user redirection
        """
        return self.auth_manager.build_auth_url(scope)
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code received after user consent
            
        Returns:
            Dictionary with access_token, refresh_token, expires_at, athlete
            
        Raises:
            StravaAuthException: If code exchange fails
        """
        tokens = self.auth_manager.exchange_token(code)
        self.tokens = tokens
        
        # Get athlete information
        athlete_data = self.get_athlete()
        
        return {
            'access_token': tokens.access_token,
            'refresh_token': tokens.refresh_token,
            'expires_at': tokens.expires_at,
            'token_type': tokens.token_type,
            'scope': tokens.scope,
            'athlete': athlete_data
        }
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh expired access token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary with new access_token, refresh_token, expires_at
            
        Raises:
            StravaTokenExpiredException: If refresh token is invalid
        """
        tokens = self.auth_manager.refresh_token(refresh_token)
        self.tokens = tokens
        
        return {
            'access_token': tokens.access_token,
            'refresh_token': tokens.refresh_token,
            'expires_at': tokens.expires_at,
            'token_type': tokens.token_type,
            'scope': tokens.scope
        }
    
    def set_access_token(self, access_token: str, refresh_token: str = None, expires_at: int = None):
        """
        Set access token manually
        
        Args:
            access_token: Valid access token
            refresh_token: Refresh token (optional)
            expires_at: Token expiration timestamp (optional)
        """
        if expires_at is None:
            expires_at = int(time.time()) + 21600  # 6 hours default
        
        self.tokens = StravaTokens(
            access_token=access_token,
            refresh_token=refresh_token or '',
            expires_at=expires_at
        )
    
    def is_token_expired(self) -> bool:
        """
        Check if current access token is expired
        
        Returns:
            True if token is expired or missing
        """
        if not self.tokens:
            return True
        return self.tokens.is_expired
    
    def get_rate_limit_status(self) -> Dict[str, int]:
        """
        Get current rate limit status
        
        Returns:
            Dictionary with rate limit information
        """
        now = time.time()
        
        # Reset counters if time window has passed
        if now >= self._rate_limit_15min['reset_time']:
            self._rate_limit_15min = {'count': 0, 'reset_time': now + 900}
        
        if now >= self._rate_limit_daily['reset_time']:
            self._rate_limit_daily = {'count': 0, 'reset_time': now + 86400}
        
        return {
            'requests_15min': self._rate_limit_15min['count'],
            'limit_15min': 100,
            'requests_daily': self._rate_limit_daily['count'],
            'limit_daily': 1000,
            'reset_15min': int(self._rate_limit_15min['reset_time']),
            'reset_daily': int(self._rate_limit_daily['reset_time'])
        }
    
    # === Private API Request Methods ===
    
    def _ensure_valid_token(self) -> str:
        """
        Ensure we have a valid access token, refresh if necessary
        
        Returns:
            Valid access token
            
        Raises:
            StravaAuthException: If no token available or refresh fails
        """
        if not self.tokens:
            raise StravaAuthException("No access token available")
        
        # Check if token needs refreshing (5 minute buffer)
        if self.tokens.is_expired and self.tokens.refresh_token:
            try:
                self.refresh_access_token(self.tokens.refresh_token)
            except Exception as e:
                raise StravaTokenExpiredException(f"Failed to refresh token: {e}")
        
        if not self.tokens.access_token:
            raise StravaAuthException("No valid access token available")
        
        return self.tokens.access_token
    
    def _make_authenticated_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make authenticated request to Strava API with rate limiting and error handling
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests
            
        Returns:
            API response as dictionary
            
        Raises:
            StravaAPIException: For API errors
            StravaRateLimitException: For rate limit errors
            StravaNetworkException: For network errors
        """
        token = self._ensure_valid_token()
        
        # Check rate limits
        rate_status = self.get_rate_limit_status()
        if rate_status['requests_15min'] >= 100:
            wait_time = rate_status['reset_15min'] - time.time()
            raise StravaRateLimitException(
                f"15-minute rate limit exceeded. Wait {int(wait_time)} seconds.",
                retry_after=int(wait_time)
            )
        
        if rate_status['requests_daily'] >= 1000:
            wait_time = rate_status['reset_daily'] - time.time()
            raise StravaRateLimitException(
                f"Daily rate limit exceeded. Wait {int(wait_time)} seconds.",
                retry_after=int(wait_time)
            )
        
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {token}'
        
        url = f"{self.API_BASE_URL}{endpoint}"
        
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            
            # Update rate limit counters
            self._rate_limit_15min['count'] += 1
            self._rate_limit_daily['count'] += 1
            
            # Handle rate limit response
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise StravaRateLimitException(
                    "Rate limit exceeded",
                    retry_after=retry_after
                )
            
            # Handle auth errors
            if response.status_code == 401:
                # Try token refresh once
                if self.tokens and self.tokens.refresh_token:
                    try:
                        self.refresh_access_token(self.tokens.refresh_token)
                        headers['Authorization'] = f'Bearer {self.tokens.access_token}'
                        response = requests.request(method, url, headers=headers, **kwargs)
                        self._rate_limit_15min['count'] += 1
                        self._rate_limit_daily['count'] += 1
                    except Exception:
                        raise StravaAuthException("Authentication failed and token refresh failed")
                else:
                    raise StravaAuthException("Authentication failed")
            
            # Handle not found
            if response.status_code == 404:
                raise StravaDataNotFoundException(f"Resource not found: {endpoint}")
            
            # Handle other client/server errors
            if response.status_code >= 400:
                error_data = None
                try:
                    error_data = response.json()
                except:
                    pass
                
                raise StravaAPIException(
                    f"API error {response.status_code}: {response.text}",
                    status_code=response.status_code,
                    response_data=error_data
                )
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise StravaNetworkException(f"Network error: {e}")
    
    # === Public API Methods ===
    
    def get_athlete(self) -> Dict[str, Any]:
        """
        Get current authenticated athlete information
        
        Returns:
            Dictionary with athlete information
        """
        return self._make_authenticated_request('GET', '/athlete')
    
    def get_athlete_stats(self) -> Dict[str, Any]:
        """
        Get athlete statistics (all-time totals, recent totals, year-to-date)
        
        Returns:
            Dictionary with athlete statistics
        """
        athlete = self.get_athlete()
        athlete_id = athlete['id']
        return self._make_authenticated_request('GET', f'/athletes/{athlete_id}/stats')
    
    def get_athlete_activities(self, before: int = None, after: int = None, 
                              page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """
        Get athlete's activities with pagination and date filtering
        
        Args:
            before: Unix timestamp - activities before this date
            after: Unix timestamp - activities after this date  
            page: Page number (starts at 1)
            per_page: Number of activities per page (max 200)
            
        Returns:
            List of activity dictionaries
        """
        params = {
            'page': page,
            'per_page': min(per_page, 200)
        }
        
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        
        return self._make_authenticated_request('GET', '/athlete/activities', params=params)
    
    def get_activity_by_id(self, activity_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific activity
        
        Args:
            activity_id: Strava activity ID
            
        Returns:
            Dictionary with detailed activity information
        """
        return self._make_authenticated_request('GET', f'/activities/{activity_id}')
    
    def get_activity_streams(self, activity_id: int, keys: List[str] = None, 
                           key_by_type: bool = True) -> Dict[str, Any]:
        """
        Get activity streams (GPS, speed, heart rate, etc.)
        
        Args:
            activity_id: Strava activity ID
            keys: List of stream types to retrieve
            key_by_type: Return data keyed by stream type
            
        Returns:
            Dictionary with stream data
        """
        if keys is None:
            keys = ['latlng', 'distance', 'time', 'altitude']
        
        params = {
            'keys': ','.join(keys),
            'key_by_type': key_by_type,
            'series_type': 'time'
        }
        
        return self._make_authenticated_request(
            'GET', 
            f'/activities/{activity_id}/streams',
            params=params
        )
    
    def get_activity_zones(self, activity_id: int) -> List[Dict[str, Any]]:
        """
        Get activity zones (power, heart rate zones)
        
        Args:
            activity_id: Strava activity ID
            
        Returns:
            List of zone dictionaries
        """
        return self._make_authenticated_request('GET', f'/activities/{activity_id}/zones')
    
    def get_activity_laps(self, activity_id: int) -> List[Dict[str, Any]]:
        """
        Get activity laps/splits
        
        Args:
            activity_id: Strava activity ID
            
        Returns:
            List of lap dictionaries
        """
        return self._make_authenticated_request('GET', f'/activities/{activity_id}/laps')
    
    # === Activity Parsing Methods ===
    
    def get_activity_full_details(self, activity_id: int) -> Dict[str, Any]:
        """
        Get complete activity data combining multiple API calls
        
        Args:
            activity_id: Strava activity ID
            
        Returns:
            Dictionary with complete activity information
        """
        # Get base activity details
        activity = self.get_activity_by_id(activity_id)
        
        # Add streams data
        try:
            streams = self.get_activity_streams(activity_id)
            activity['streams'] = streams
            
            # Add GPS coordinates if available
            if 'latlng' in streams and 'data' in streams['latlng']:
                activity['coordinates'] = streams['latlng']['data']
            
            # Add altitude data if available
            if 'altitude' in streams and 'data' in streams['altitude']:
                activity['altitudes'] = streams['altitude']['data']
                
            # Add time and distance data
            if 'time' in streams and 'data' in streams['time']:
                activity['times'] = streams['time']['data']
                
            if 'distance' in streams and 'data' in streams['distance']:
                activity['distances'] = streams['distance']['data']
                activity['distances_km'] = [d / 1000.0 for d in streams['distance']['data']]
        except Exception:
            # Continue without streams if not available
            pass
        
        # Add laps data
        try:
            laps = self.get_activity_laps(activity_id)
            activity['laps'] = laps
        except Exception:
            pass
        
        # Add zones data  
        try:
            zones = self.get_activity_zones(activity_id)
            activity['zones'] = zones
        except Exception:
            pass
        
        return activity
    
    def parse_activity_full(self, activity_id: int) -> Dict[str, Any]:
        """
        Main method that aggregates all activity data (replaces activity_full_parser)
        
        Args:
            activity_id: Strava activity ID
            
        Returns:
            Dictionary with complete parsed activity data
        """
        return self.get_activity_full_details(activity_id)
    
    # === Utility Methods ===
    
    def get_all_activities(self, after: int = None, before: int = None, 
                          max_activities: int = None) -> List[Dict[str, Any]]:
        """
        Get all athlete activities with automatic pagination
        
        Args:
            after: Unix timestamp - activities after this date
            before: Unix timestamp - activities before this date
            max_activities: Maximum number of activities to retrieve
            
        Returns:
            List of all activity dictionaries
        """
        all_activities = []
        page = 1
        per_page = 200
        
        while True:
            activities = self.get_athlete_activities(
                before=before, after=after, page=page, per_page=per_page
            )
            
            if not activities:
                break
            
            all_activities.extend(activities)
            
            if max_activities and len(all_activities) >= max_activities:
                all_activities = all_activities[:max_activities]
                break
            
            if len(activities) < per_page:
                break
            
            page += 1
            time.sleep(0.1)  # Respect rate limits
        
        return all_activities
    
    def get_activities_by_year(self, year: int) -> List[Dict[str, Any]]:
        """Get all activities for a specific year"""
        start_of_year = datetime(year, 1, 1)
        end_of_year = datetime(year + 1, 1, 1)
        
        after = int(start_of_year.timestamp())
        before = int(end_of_year.timestamp())
        
        return self.get_all_activities(after=after, before=before)
    
    def get_activities_by_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Get all activities for a specific month"""
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        
        start_of_month = datetime(year, month, 1)
        
        after = int(start_of_month.timestamp())
        before = int(next_month.timestamp())
        
        return self.get_all_activities(after=after, before=before)
    
    def get_activity_gpx_data(self, activity_id: int) -> Optional[List[List[float]]]:
        """
        Get GPS coordinates for map display
        
        Args:
            activity_id: Strava activity ID
            
        Returns:
            List of [latitude, longitude] coordinates or None
        """
        try:
            streams = self.get_activity_streams(activity_id, ['latlng'])
            
            if 'latlng' in streams and 'data' in streams['latlng']:
                return streams['latlng']['data']
            return None
            
        except Exception:
            return None