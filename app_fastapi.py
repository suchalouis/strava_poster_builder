#!/usr/bin/env python3
"""
Point d'entrée FastAPI utilisant la nouvelle architecture project-strava-api
"""

import os
import sys
from pathlib import Path

# Ajouter project-strava-api au path Python
project_root = Path(__file__).parent / "project-strava-api"
sys.path.insert(0, str(project_root))

# Maintenant on peut importer depuis project-strava-api
from app.main import app
from app.config import settings

if __name__ == '__main__':
    import uvicorn
    
    # Vérifier les variables d'environnement requises
    if not settings.strava_client_id or not settings.strava_client_secret:
        print("ERROR: Please configure STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in .env file")
        sys.exit(1)
    
    print(f"Starting FastAPI Strava API...")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    print(f"Redirect URI: {settings.strava_redirect_uri}")
    print(f"API docs: http://localhost:8000/docs" if settings.debug else "API docs disabled in production")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )