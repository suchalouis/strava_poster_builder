#!/usr/bin/env python3
"""
Main Flask application entry point
"""

import os
import secrets
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv

load_dotenv()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Security configuration
    app.config['SECRET_KEY'] = os.getenv('SESSION_SECRET_KEY', secrets.token_hex(32))
    
    # Try Redis, fallback to filesystem
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    try:
        import redis
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()  # Test connection
        app.config['SESSION_TYPE'] = 'redis'
        app.config['SESSION_REDIS'] = redis_client
        print("Using Redis for sessions")
    except Exception as e:
        print("WARNING: Redis not available, using filesystem sessions")
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = '/tmp/flask_sessions'
        
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP in development
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_NAME'] = 'strava_session'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours in seconds
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Enable CORS for all routes (with credentials for cookies)
    CORS(app, origins=["file://", "http://localhost:*", "http://127.0.0.1:*"], 
         supports_credentials=True)
    
    # Initialize session
    Session(app)
    
    # Import and register routes
    from src.strava.auth_server import register_routes
    register_routes(app)
    
    return app

app = create_app()

if __name__ == '__main__':
    # OAuth configuration from environment
    STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
    STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
    STRAVA_REDIRECT_URI = os.getenv('STRAVA_REDIRECT_URI', 'http://localhost:8000/auth/callback')
    
    if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET:
        print("ERROR: Please configure STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in .env file")
        exit(1)
    
    print(f"Starting Strava OAuth server...")
    print(f"Redirect URI: {STRAVA_REDIRECT_URI}")
    app.run(host='0.0.0.0', port=8000, debug=True)