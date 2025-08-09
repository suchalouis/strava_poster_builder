#!/usr/bin/env python3
"""
Main Flask application entry point
"""

import os
import secrets
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(32)
    
    # Enable CORS for all routes
    CORS(app, origins=["file://", "http://localhost:*", "http://127.0.0.1:*"])
    
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