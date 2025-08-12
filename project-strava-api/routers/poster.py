"""
Routes pour la génération de posters
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.dependencies import get_current_active_user, get_poster_service
from models.user import User
from schemas.poster import (
    PosterConfigResponse,
    PosterConfigCreate,
    PosterConfigUpdate,
    PosterGenerationRequest,
    PosterGenerationResponse,
    PosterHistoryResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/configs", response_model=List[PosterConfigResponse])
async def get_poster_configs(
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupérer les configurations de poster de l'utilisateur
    """
    # TODO: Implémenter avec PosterService
    return []


@router.post("/configs", response_model=PosterConfigResponse)
async def create_poster_config(
    config: PosterConfigCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Créer une nouvelle configuration de poster
    """
    # TODO: Implémenter avec PosterService
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Poster configuration creation not implemented yet"
    )


@router.put("/configs/{config_id}", response_model=PosterConfigResponse)
async def update_poster_config(
    config_id: int,
    config_update: PosterConfigUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Mettre à jour une configuration de poster
    """
    # TODO: Implémenter avec PosterService
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Poster configuration update not implemented yet"
    )


@router.post("/generate", response_model=PosterGenerationResponse)
async def generate_poster(
    request: PosterGenerationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Générer un poster avec la configuration spécifiée
    """
    # TODO: Implémenter avec PosterService
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Poster generation not implemented yet"
    )


@router.get("/history", response_model=PosterHistoryResponse)
async def get_poster_history(
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupérer l'historique des posters générés
    """
    # TODO: Implémenter avec PosterService
    return PosterHistoryResponse(posters=[], total=0)


@router.get("/{poster_id}/download")
async def download_poster(
    poster_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Télécharger un poster généré
    """
    # TODO: Implémenter avec PosterService
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Poster download not implemented yet"
    )