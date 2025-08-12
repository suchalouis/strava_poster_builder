"""
Routes pour les activités Strava
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any

from app.dependencies import get_strava_service
from services.strava_service import StravaService
from schemas.strava import (
    ActivitiesResponse, 
    ActivityDetail, 
    ActivitySummaryResponse,
    ActivityFilters,
    GPXDataResponse,
    MultipleGPXResponse
)
from strava import StravaAPIException
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=ActivitiesResponse)
async def get_activities(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(30, ge=1, le=200, description="Items per page"),
    before: Optional[int] = Query(None, description="Unix timestamp - activities before this date"),
    after: Optional[int] = Query(None, description="Unix timestamp - activities after this date"),
    strava_service: StravaService = Depends(get_strava_service)
):
    """
    Récupérer la liste des activités de l'utilisateur avec pagination
    """
    try:
        activities = await strava_service.get_activities(
            before=before,
            after=after,
            page=page,
            per_page=per_page
        )

        logger.info(f"{len(activities)} activity/ies retrieved")

        return ActivitiesResponse(
            activities=activities,
            total=len(activities),
            page=page,
            per_page=per_page
        )
        
    except StravaAPIException as e:
        logger.error(f"Strava API error getting activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Strava API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activities"
        )


@router.get("/{activity_id}", response_model=ActivityDetail)
async def get_activity_detail(
    activity_id: int,
    strava_service: StravaService = Depends(get_strava_service)
):
    """
    Récupérer les détails complets d'une activité spécifique
    """
    try:
        activity = await strava_service.get_activity_detail(activity_id)
        logger.info(f"Activity {activity_id} details retrieved")
        return ActivityDetail(**activity)
        
    except StravaAPIException as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity {activity_id} not found"
            )
        logger.error(f"Strava API error getting activity {activity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Strava API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting activity {activity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity details"
        )


@router.get("/summary", response_model=ActivitySummaryResponse)
async def get_activities_summary(
    year: Optional[int] = Query(None, ge=2008, le=2030, description="Filter by year"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month (requires year)"),
    max_activities: Optional[int] = Query(None, ge=1, le=1000, description="Maximum number of activities"),
    strava_service: StravaService = Depends(get_strava_service)
):
    """
    Récupérer un résumé complet des activités avec statistiques
    """
    try:
        if month and not year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Year is required when filtering by month"
            )
        
        summary = await strava_service.get_activities_summary(
            year=year,
            month=month,
            max_activities=max_activities
        )
        
        return ActivitySummaryResponse(**summary)
        
    except StravaAPIException as e:
        logger.error(f"Strava API error getting activities summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Strava API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting activities summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activities summary"
        )


@router.get("/year/{year}")
async def get_activities_by_year(
    year: int,
    strava_service: StravaService = Depends(get_strava_service)
):
    """
    Récupérer toutes les activités d'une année donnée
    """
    try:
        if year < 2008 or year > 2030:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Year must be between 2008 and 2030"
            )
        
        activities = await strava_service.get_activities_by_year(year)
        
        return {
            "year": year,
            "activities": activities,
            "total": len(activities)
        }
        
    except StravaAPIException as e:
        logger.error(f"Strava API error getting activities for year {year}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Strava API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting activities for year {year}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activities by year"
        )


@router.get("/{activity_id}/gpx", response_model=GPXDataResponse)
async def get_activity_gpx(
    activity_id: int,
    strava_service: StravaService = Depends(get_strava_service)
):
    """
    Récupérer les données GPS d'une activité spécifique
    """
    try:
        gpx_data = await strava_service.get_activity_gpx_data(activity_id)
        
        if not gpx_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No GPS data available for activity {activity_id}"
            )
        
        return GPXDataResponse(
            activity_id=activity_id,
            coordinates=gpx_data,
            total_points=len(gpx_data)
        )
        
    except StravaAPIException as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity {activity_id} not found"
            )
        logger.error(f"Strava API error getting GPX for activity {activity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Strava API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting GPX for activity {activity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve GPS data"
        )


@router.get("/gpx/multiple", response_model=MultipleGPXResponse)
async def get_multiple_activities_gpx(
    activity_ids: str = Query(..., description="Comma-separated list of activity IDs"),
    strava_service: StravaService = Depends(get_strava_service)
):
    """
    Récupérer les données GPS de plusieurs activités
    """
    try:
        # Parser les IDs d'activité
        try:
            ids = [int(id.strip()) for id in activity_ids.split(',') if id.strip()]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid activity IDs format"
            )
        
        if len(ids) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No activity IDs provided"
            )
        
        if len(ids) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 20 activities per request"
            )
        
        activities_gpx = await strava_service.get_multiple_activities_gpx(ids)
        
        return MultipleGPXResponse(
            activities=[
                GPXDataResponse(**activity) for activity in activities_gpx
            ],
            total=len(activities_gpx)
        )
        
    except StravaAPIException as e:
        logger.error(f"Strava API error getting multiple GPX: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Strava API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting multiple activities GPX: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve GPS data"
        )