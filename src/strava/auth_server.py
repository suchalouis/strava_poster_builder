#!/usr/bin/env python3
"""
Backend OAuth server for Strava authentication
Handles OAuth flow securely with environment variables
"""

import os
import secrets
import urllib.parse
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Enable CORS for all routes
CORS(app, origins=["file://", "http://localhost:*", "http://127.0.0.1:*"])

# OAuth configuration from environment
STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
STRAVA_REDIRECT_URI = os.getenv('STRAVA_REDIRECT_URI', 'http://localhost:8000/auth/callback')

# Strava OAuth endpoints
STRAVA_AUTH_URL = 'https://www.strava.com/oauth/authorize'
STRAVA_TOKEN_URL = 'https://www.strava.com/oauth/token'

# In-memory storage for OAuth states (use Redis/database in production)
oauth_states = {}

@app.route('/')
def serve_auth_page():
    """Serve the auth page"""
    try:
        with open('src/front/auth_page.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Auth page not found", 404

@app.route('/auth')
def serve_auth_page_explicit():
    """Serve the auth page via /auth route"""
    return serve_auth_page()

@app.route('/home')
def serve_home_page():
    """Serve the home page for authenticated users"""
    try:
        with open('src/front/home.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Home page not found", 404

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'strava-oauth-server'})

@app.route('/auth/config')
def get_auth_config():
    """Get OAuth configuration for frontend (without sensitive data)"""
    if not STRAVA_CLIENT_ID:
        return jsonify({'error': 'OAuth not configured'}), 500
    
    return jsonify({
        'client_id': STRAVA_CLIENT_ID,
        'redirect_uri': STRAVA_REDIRECT_URI,
        'scope': 'read,activity:read_all,profile:read_all'
    })

@app.route('/auth/initiate')
def initiate_auth():
    """Initiate OAuth flow"""
    if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET:
        return jsonify({'error': 'OAuth credentials not configured'}), 500
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {'timestamp': secrets.SystemRandom().randint(1000000, 9999999)}
    
    # Build authorization URL
    params = {
        'client_id': STRAVA_CLIENT_ID,
        'redirect_uri': STRAVA_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'read,activity:read_all,profile:read_all',
        'approval_prompt': 'auto',
        'state': state
    }
    
    auth_url = f"{STRAVA_AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    return jsonify({'auth_url': auth_url, 'state': state})

@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Strava"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return render_template_string("""
        <html>
        <head><title>Erreur d'authentification</title></head>
        <body>
            <h1>Erreur d'authentification</h1>
            <p>{{ error }}</p>
            <script>
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'strava_auth_error',
                        error: '{{ error }}'
                    }, 'http://localhost:8000');
                }
                setTimeout(() => {
                    window.close();
                }, 3000);
            </script>
        </body>
        </html>
        """, error=error), 400
    
    if not code or not state:
        return jsonify({'error': 'Missing authorization code or state'}), 400
    
    # Verify state
    if state not in oauth_states:
        return jsonify({'error': 'Invalid state parameter'}), 400
    
    # Remove used state
    del oauth_states[state]
    
    try:
        # Exchange code for tokens
        token_data = exchange_code_for_tokens(code)
        
        # Return popup callback page that sends message to parent window
        return render_template_string("""
        <html>
        <head>
            <title>Authentification réussie</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 2rem;
                    background: linear-gradient(135deg, #fc4c02, #ff6b35);
                    color: white;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .success { 
                    background: rgba(255,255,255,0.1);
                    padding: 2rem;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                .checkmark {
                    font-size: 4rem;
                    margin-bottom: 1rem;
                }
            </style>
        </head>
        <body>
            <div class="success">
                <div class="checkmark">✅</div>
                <h1>Authentification réussie !</h1>
                <p>Cette fenêtre va se fermer automatiquement...</p>
            </div>
            
            <script>
                // Send success message to parent window
                const tokenData = {
                    access_token: '{{ access_token }}',
                    refresh_token: '{{ refresh_token }}',
                    expires_at: {{ expires_at }},
                    athlete: {{ athlete | tojson }}
                };
                
                if (window.opener) {
                    // Send message to parent window
                    window.opener.postMessage({
                        type: 'strava_auth_success',
                        data: tokenData
                    }, '{{ origin }}');
                    
                    // Close popup after short delay
                    setTimeout(() => {
                        window.close();
                    }, 1500);
                } else {
                    // Fallback: store in localStorage and redirect
                    localStorage.setItem('strava_auth', JSON.stringify(tokenData));
                    window.location.href = '/home';
                }
            </script>
        </body>
        </html>
        """, 
        access_token=token_data['access_token'],
        refresh_token=token_data['refresh_token'],
        expires_at=token_data['expires_at'],
        athlete=token_data['athlete'],
        origin='http://localhost:8000'
        )
        
    except Exception as e:
        return render_template_string("""
        <html><head><title>Auth Error</title></head>
        <body><h1>Authentication Error</h1><p>{{ error }}</p>
        <script>
            setTimeout(() => {
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'strava_auth_error',
                        error: '{{ error }}'
                    }, '*');
                    window.close();
                }
            }, 3000);
        </script>
        </body></html>
        """, error=str(e)), 500

@app.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token"""
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'Refresh token required'}), 400
    
    try:
        response = requests.post(STRAVA_TOKEN_URL, data={
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        })
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to refresh token'}), 400
        
        return jsonify(response.json())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def exchange_code_for_tokens(code):
    """Exchange authorization code for access tokens"""
    response = requests.post(STRAVA_TOKEN_URL, data={
        'client_id': STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    })
    
    if response.status_code != 200:
        raise Exception(f'Token exchange failed: {response.text}')
    
    return response.json()

if __name__ == '__main__':
    if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET:
        print("ERROR: Please configure STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in .env file")
        exit(1)
    
    print(f"Starting Strava OAuth server...")
    print(f"Redirect URI: {STRAVA_REDIRECT_URI}")
    app.run(host='0.0.0.0', port=8000, debug=True)