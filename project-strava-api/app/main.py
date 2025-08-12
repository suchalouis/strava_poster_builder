"""
Point d'entrée principal de l'application FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.config import settings
from core.middleware import setup_middleware
from routers import auth, activities, athlete, poster, frontend
import logging

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Factory pour créer l'application FastAPI
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        debug=settings.debug,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json" if settings.debug else None,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Middlewares personnalisés
    setup_middleware(app)
    
    # Static files
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Templates
    templates_dir = Path(__file__).parent.parent / "templates"
    if templates_dir.exists():
        templates = Jinja2Templates(directory=str(templates_dir))
        app.state.templates = templates
    
    # Routers
    app.include_router(
        auth.router,
        prefix=f"{settings.api_v1_prefix}/auth",
        tags=["Authentification"]
    )
    app.include_router(
        athlete.router,
        prefix=f"{settings.api_v1_prefix}/athlete",
        tags=["Athlete"]
    )
    app.include_router(
        activities.router,
        prefix=f"{settings.api_v1_prefix}/activities",
        tags=["Activities"]
    )
    app.include_router(
        poster.router,
        prefix=f"{settings.api_v1_prefix}/poster",
        tags=["Poster"]
    )
    
    # Frontend routes (templates) - no API prefix
    app.include_router(
        frontend.router,
        tags=["Frontend"]
    )
    
    # Event handlers
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting {settings.app_name} v{settings.version}")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info("Running without database - using in-memory storage")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down application")
    
    # Health check
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.version,
            "environment": settings.environment
        }
    
    return app


# Instance de l'application
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )