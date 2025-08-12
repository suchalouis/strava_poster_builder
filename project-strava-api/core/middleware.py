"""
Middlewares personnalisés pour l'application FastAPI
"""

import time
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging

from app.config import settings

logger = logging.getLogger(__name__)


def setup_middleware(app: FastAPI) -> None:
    """
    Configure tous les middlewares de l'application
    """
    
    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next: Callable) -> Response:
        """Ajouter un ID unique à chaque requête"""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    
    # Logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable) -> Response:
        """Logger les requêtes"""
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.4f}s - "
            f"Request-ID: {getattr(request.state, 'request_id', 'unknown')}"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next: Callable) -> Response:
        """Ajouter des headers de sécurité"""
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
    
    # Rate limiting middleware (basique)
    @app.middleware("http") 
    async def rate_limiting(request: Request, call_next: Callable) -> Response:
        """Rate limiting basique (à améliorer avec Redis)"""
        # Pour l'instant, on passe toutes les requêtes
        # TODO: Implémenter un vrai rate limiting avec Redis
        return await call_next(request)
    
    # Trusted hosts
    if settings.allowed_hosts != ["*"]:
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=settings.allowed_hosts
        )
    
    # Compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    logger.info("Middlewares configured successfully")