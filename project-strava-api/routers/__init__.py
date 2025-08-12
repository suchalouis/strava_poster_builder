"""
Routers FastAPI pour l'API Strava Poster
"""

from . import auth, activities, athlete, poster, frontend

__all__ = ['auth', 'activities', 'athlete', 'poster', 'frontend']