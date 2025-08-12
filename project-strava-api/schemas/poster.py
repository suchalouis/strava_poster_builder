"""
Schémas Pydantic pour les posters
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PosterFormat(str, Enum):
    """Formats de poster supportés"""
    PDF = "pdf"
    PNG = "png"
    JPEG = "jpeg"


class PosterTemplate(str, Enum):
    """Templates de poster disponibles"""
    CLASSIC = "classic"
    MODERN = "modern"
    MINIMALIST = "minimalist"
    ATHLETIC = "athletic"


class ColorScheme(str, Enum):
    """Schémas de couleur disponibles"""
    ORANGE = "orange"
    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"
    RED = "red"
    BLACK = "black"


class PosterConfigBase(BaseModel):
    """Configuration de base pour un poster"""
    name: str = Field(min_length=1, max_length=200)
    template: PosterTemplate = PosterTemplate.CLASSIC
    format: PosterFormat = PosterFormat.PDF
    
    # Paramètres de contenu
    year: Optional[int] = Field(None, ge=2008, le=2030)
    activity_types: Optional[List[str]] = None
    include_photos: bool = True
    include_maps: bool = True
    include_stats: bool = True
    include_elevation: bool = True
    
    # Style
    color_scheme: ColorScheme = ColorScheme.ORANGE
    background_color: str = Field("#FFFFFF", pattern="^#[0-9A-Fa-f]{6}$")
    text_color: str = Field("#000000", pattern="^#[0-9A-Fa-f]{6}$")
    
    # Paramètres personnalisés
    custom_settings: Optional[Dict[str, Any]] = None
    
    @validator('activity_types')
    def validate_activity_types(cls, v):
        if v is not None:
            valid_types = [
                'Run', 'Ride', 'Swim', 'Hike', 'Walk', 'WeightTraining', 
                'Workout', 'Yoga', 'AlpineSki', 'BackcountrySki', 'Snowboard'
            ]
            for activity_type in v:
                if activity_type not in valid_types:
                    raise ValueError(f"Invalid activity type: {activity_type}")
        return v


class PosterConfigCreate(PosterConfigBase):
    """Schéma pour créer une configuration de poster"""
    pass


class PosterConfigUpdate(BaseModel):
    """Schéma pour mettre à jour une configuration de poster"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    template: Optional[PosterTemplate] = None
    format: Optional[PosterFormat] = None
    year: Optional[int] = Field(None, ge=2008, le=2030)
    activity_types: Optional[List[str]] = None
    include_photos: Optional[bool] = None
    include_maps: Optional[bool] = None
    include_stats: Optional[bool] = None
    include_elevation: Optional[bool] = None
    color_scheme: Optional[ColorScheme] = None
    background_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    text_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    custom_settings: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class PosterConfigResponse(PosterConfigBase):
    """Réponse pour une configuration de poster"""
    id: int
    user_id: int
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PosterGenerationRequest(BaseModel):
    """Requête pour générer un poster"""
    config_id: Optional[int] = None
    config: Optional[PosterConfigBase] = None
    
    @validator('config_id', 'config')
    def validate_config_or_id(cls, v, values):
        config_id = values.get('config_id')
        config = values.get('config') 
        
        if not config_id and not config:
            raise ValueError("Either config_id or config must be provided")
        if config_id and config:
            raise ValueError("Cannot provide both config_id and config")
        
        return v


class PosterGenerationResponse(BaseModel):
    """Réponse de génération de poster"""
    poster_id: int
    filename: str
    file_size: int
    generation_time: int
    activities_count: int
    download_url: str
    expires_at: Optional[datetime] = None


class GeneratedPosterResponse(BaseModel):
    """Informations sur un poster généré"""
    id: int
    user_id: int
    config_id: Optional[int] = None
    filename: str
    file_size: Optional[int] = None
    activities_count: Optional[int] = None
    generation_time: Optional[int] = None
    download_count: int
    is_available: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    download_url: str
    
    class Config:
        from_attributes = True


class PosterHistoryResponse(BaseModel):
    """Historique des posters générés"""
    posters: List[GeneratedPosterResponse]
    total: int