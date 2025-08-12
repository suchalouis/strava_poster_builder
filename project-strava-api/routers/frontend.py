"""
Routes pour servir les pages front-end
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.dependencies import get_current_active_user
from models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Templates directory
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/", response_class=HTMLResponse)
async def root_page(request: Request):
    """
    Page d'accueil - redirige vers la page d'authentification
    """
    return templates.TemplateResponse("auth_page.html", {"request": request})


@router.get("/auth", response_class=HTMLResponse) 
async def auth_page(request: Request):
    """
    Page d'authentification Strava
    """
    return templates.TemplateResponse("auth_page.html", {"request": request})


@router.get("/home", response_class=HTMLResponse)
async def home_page(request: Request):
    """
    Page d'accueil principale (dashboard) - nécessite une authentification
    """
    try:
        # Vérifier si l'utilisateur est connecté côté serveur
        # Pour l'instant, on sert la page sans vérification stricte
        # La vérification se fait côté client JavaScript
        return templates.TemplateResponse("home.html", {"request": request})
    except Exception as e:
        logger.error(f"Error serving home page: {e}")
        # En cas d'erreur, rediriger vers la page d'authentification
        return templates.TemplateResponse("auth_page.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Alias pour la page d'accueil
    """
    return await home_page(request)


@router.get("/auth/callback")
async def oauth_callback_redirect(request: Request):
    """
    Redirection OAuth callback vers l'API
    Strava redirige vers /auth/callback, on redirige vers /api/v1/auth/callback
    """
    # Récupérer tous les paramètres de query string
    query_params = str(request.url.query)
    
    # Rediriger vers la vraie route callback de l'API
    callback_url = f"/api/v1/auth/callback"
    if query_params:
        callback_url += f"?{query_params}"
    
    logger.info(f"Redirecting OAuth callback to API: {callback_url}")
    return RedirectResponse(url=callback_url, status_code=302)