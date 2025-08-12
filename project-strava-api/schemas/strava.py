"""
Schémas Pydantic pour les données Strava
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class AthleteResponse(BaseModel):
    """Réponse pour les informations d'athlète"""
    id: int
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    full_name: Optional[str] = None
    profile: Optional[str] = None
    profile_medium: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    sex: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ActivitySummary(BaseModel):
    """Résumé d'une activité"""
    id: int
    name: str
    type: str
    icon: Optional[str] = None
    distance: str
    time: str
    elevation: str
    date: Optional[str] = None
    formatted_date: Optional[str] = None
    
    # Données brutes pour les calculs (correspondent aux clés du service)
    distance_raw: float
    moving_time: int  
    total_elevation_gain: float


class ActivityDetail(ActivitySummary):
    """Détails complets d'une activité"""
    start_latlng: Optional[List[float]] = None
    end_latlng: Optional[List[float]] = None
    average_speed: Optional[float] = None
    max_speed: Optional[float] = None
    average_heartrate: Optional[float] = None
    max_heartrate: Optional[float] = None
    elev_high: Optional[float] = None
    elev_low: Optional[float] = None
    coordinates: Optional[List[List[float]]] = None
    altitudes: Optional[List[float]] = None
    distances: Optional[List[float]] = None
    times: Optional[List[int]] = None


class ActivitiesResponse(BaseModel):
    """Réponse pour une liste d'activités"""
    activities: List[ActivitySummary]
    total: int
    page: int = 1
    per_page: int = 30


class ActivityStatsResponse(BaseModel):
    """Statistiques d'activités"""
    total_activities: int
    total_distance: str
    total_time: str
    total_elevation: str
    by_sport: Dict[str, Dict[str, Any]]


class ActivitySummaryResponse(BaseModel):
    """Résumé complet des activités avec statistiques"""
    summary: ActivityStatsResponse
    recent_activities: List[ActivitySummary]
    monthly_stats: Optional[Dict[str, Dict[str, Any]]] = None
    weekly_stats: Optional[Dict[str, Any]] = None
    personal_records: Optional[Dict[str, Any]] = None


class GPXDataResponse(BaseModel):
    """Données GPX pour une activité"""
    activity_id: int
    coordinates: List[List[float]]
    total_points: int = Field(description="Nombre total de points GPS")


class MultipleGPXResponse(BaseModel):
    """Données GPX pour plusieurs activités"""
    activities: List[GPXDataResponse]
    total: int


class ActivityFilters(BaseModel):
    """Filtres pour les activités"""
    activity_types: Optional[List[str]] = None
    year: Optional[int] = None
    month: Optional[int] = None
    after: Optional[datetime] = None
    before: Optional[datetime] = None
    per_page: int = Field(default=30, ge=1, le=200)
    page: int = Field(default=1, ge=1)


class StreamRequest(BaseModel):
    """Requête pour les streams d'activité"""
    keys: List[str] = Field(default=["latlng", "distance", "time", "altitude"])
    key_by_type: bool = True