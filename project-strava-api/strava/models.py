"""
Data models for Strava API responses
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class StravaAthlete:
    """Strava athlete data model"""
    id: int
    firstname: str
    lastname: str
    profile: Optional[str] = None
    profile_medium: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    sex: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StravaAthlete':
        """Create StravaAthlete from API response dictionary"""
        return cls(
            id=data.get('id'),
            firstname=data.get('firstname', ''),
            lastname=data.get('lastname', ''),
            profile=data.get('profile'),
            profile_medium=data.get('profile_medium'),
            city=data.get('city'),
            country=data.get('country'),
            sex=data.get('sex'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    @property
    def full_name(self) -> str:
        """Get full name of athlete"""
        return f"{self.firstname} {self.lastname}".strip()


@dataclass
class StravaActivity:
    """Strava activity data model"""
    id: int
    name: str
    type: str
    distance: float
    moving_time: int
    elapsed_time: int
    total_elevation_gain: float
    start_date_local: str
    start_latlng: Optional[List[float]] = None
    end_latlng: Optional[List[float]] = None
    average_speed: Optional[float] = None
    max_speed: Optional[float] = None
    average_heartrate: Optional[float] = None
    max_heartrate: Optional[float] = None
    elev_high: Optional[float] = None
    elev_low: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StravaActivity':
        """Create StravaActivity from API response dictionary"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            type=data.get('type', ''),
            distance=data.get('distance', 0.0),
            moving_time=data.get('moving_time', 0),
            elapsed_time=data.get('elapsed_time', 0),
            total_elevation_gain=data.get('total_elevation_gain', 0.0),
            start_date_local=data.get('start_date_local', ''),
            start_latlng=data.get('start_latlng'),
            end_latlng=data.get('end_latlng'),
            average_speed=data.get('average_speed'),
            max_speed=data.get('max_speed'),
            average_heartrate=data.get('average_heartrate'),
            max_heartrate=data.get('max_heartrate'),
            elev_high=data.get('elev_high'),
            elev_low=data.get('elev_low')
        )
    
    @property
    def distance_km(self) -> float:
        """Get distance in kilometers"""
        return self.distance / 1000.0
    
    @property
    def pace_per_km(self) -> Optional[float]:
        """Get pace in seconds per kilometer (for running activities)"""
        if self.distance > 0 and self.type == 'Run':
            return (self.moving_time * 1000) / self.distance
        return None


@dataclass
class StravaStream:
    """Strava activity stream data model"""
    type: str
    data: List[Any]
    series_type: str
    original_size: int
    resolution: str
    
    @classmethod
    def from_dict(cls, stream_type: str, data: Dict[str, Any]) -> 'StravaStream':
        """Create StravaStream from API response dictionary"""
        return cls(
            type=stream_type,
            data=data.get('data', []),
            series_type=data.get('series_type', ''),
            original_size=data.get('original_size', 0),
            resolution=data.get('resolution', '')
        )


@dataclass
class StravaLap:
    """Strava activity lap data model"""
    id: int
    name: str
    elapsed_time: int
    moving_time: int
    start_date_local: str
    distance: float
    start_index: int
    end_index: int
    total_elevation_gain: float
    average_speed: Optional[float] = None
    max_speed: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StravaLap':
        """Create StravaLap from API response dictionary"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            elapsed_time=data.get('elapsed_time', 0),
            moving_time=data.get('moving_time', 0),
            start_date_local=data.get('start_date_local', ''),
            distance=data.get('distance', 0.0),
            start_index=data.get('start_index', 0),
            end_index=data.get('end_index', 0),
            total_elevation_gain=data.get('total_elevation_gain', 0.0),
            average_speed=data.get('average_speed'),
            max_speed=data.get('max_speed')
        )


@dataclass
class StravaSegment:
    """Strava segment data model"""
    id: int
    name: str
    activity_type: str
    distance: float
    average_grade: float
    maximum_grade: float
    elevation_high: float
    elevation_low: float
    start_latlng: List[float]
    end_latlng: List[float]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StravaSegment':
        """Create StravaSegment from API response dictionary"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            activity_type=data.get('activity_type', ''),
            distance=data.get('distance', 0.0),
            average_grade=data.get('average_grade', 0.0),
            maximum_grade=data.get('maximum_grade', 0.0),
            elevation_high=data.get('elevation_high', 0.0),
            elevation_low=data.get('elevation_low', 0.0),
            start_latlng=data.get('start_latlng', []),
            end_latlng=data.get('end_latlng', [])
        )


@dataclass
class StravaTokens:
    """Strava OAuth tokens data model"""
    access_token: str
    refresh_token: str
    expires_at: int
    token_type: str = "Bearer"
    scope: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StravaTokens':
        """Create StravaTokens from OAuth response dictionary"""
        return cls(
            access_token=data.get('access_token', ''),
            refresh_token=data.get('refresh_token', ''),
            expires_at=data.get('expires_at', 0),
            token_type=data.get('token_type', 'Bearer'),
            scope=data.get('scope', '')
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if the access token is expired (with 5 minute buffer)"""
        import time
        return time.time() >= (self.expires_at - 300)


@dataclass
class StravaActivityStats:
    """Strava activity statistics data model"""
    recent_run_totals: Dict[str, Any]
    all_run_totals: Dict[str, Any]
    recent_ride_totals: Dict[str, Any] 
    all_ride_totals: Dict[str, Any]
    recent_swim_totals: Dict[str, Any]
    all_swim_totals: Dict[str, Any]
    ytd_run_totals: Dict[str, Any]
    ytd_ride_totals: Dict[str, Any]
    ytd_swim_totals: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StravaActivityStats':
        """Create StravaActivityStats from API response dictionary"""
        return cls(
            recent_run_totals=data.get('recent_run_totals', {}),
            all_run_totals=data.get('all_run_totals', {}),
            recent_ride_totals=data.get('recent_ride_totals', {}),
            all_ride_totals=data.get('all_ride_totals', {}),
            recent_swim_totals=data.get('recent_swim_totals', {}),
            all_swim_totals=data.get('all_swim_totals', {}),
            ytd_run_totals=data.get('ytd_run_totals', {}),
            ytd_ride_totals=data.get('ytd_ride_totals', {}),
            ytd_swim_totals=data.get('ytd_swim_totals', {})
        )