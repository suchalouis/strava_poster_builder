#!/usr/bin/env python3
"""
Backend OAuth server for Strava authentication
Handles OAuth flow securely with environment variables
"""

import os
import secrets
import urllib.parse
from flask import request, jsonify, render_template_string, session, make_response, redirect
from dotenv import load_dotenv
import requests
from .strava_client import StravaClient
from .data_processor import StravaDataProcessor
from ..security import SecurityManager

load_dotenv()

# OAuth configuration from environment
STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
STRAVA_REDIRECT_URI = os.getenv('STRAVA_REDIRECT_URI', 'http://localhost:8000/auth/callback')

# Strava OAuth endpoints
STRAVA_AUTH_URL = 'https://www.strava.com/oauth/authorize'
STRAVA_TOKEN_URL = 'https://www.strava.com/oauth/token'

# Instances globales
strava_client = StravaClient()
data_processor = StravaDataProcessor()
security_manager = None  # Will be initialized in register_routes

def register_routes(app):
    """Register all routes with the Flask app"""
    global security_manager
    
    # Initialize security manager within app context
    with app.app_context():
        security_manager = SecurityManager()
    
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
        security_manager.store_oauth_state(state)
        
        # Generate CSRF token for session
        csrf_token = security_manager.generate_csrf_token()
        session['csrf_token'] = csrf_token
        
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
        
        return jsonify({'auth_url': auth_url, 'state': state, 'csrf_token': csrf_token})

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
        
        # Verify and consume OAuth state
        if not security_manager.verify_oauth_state(state):
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        try:
            # Exchange code for tokens
            token_data = exchange_code_for_tokens(code)
            
            # Store tokens securely in session
            secure_session_data = security_manager.create_secure_session_data(token_data)
            session['auth_data'] = secure_session_data
            session['authenticated'] = True
            session.permanent = True  # Make session permanent
            
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
                    // Toujours essayer de fermer la popup et envoyer un message au parent
                    // même si window.opener n'est pas détecté immédiatement
                    function closePopupAndRedirect() {
                        try {
                            if (window.opener && !window.opener.closed) {
                                // Send success message to parent window (no tokens exposed)
                                window.opener.postMessage({
                                    type: 'strava_auth_success',
                                    data: {
                                        athlete_name: '{{ athlete_name }}',
                                        authenticated: true
                                    }
                                }, '{{ origin }}');
                                
                                // Close popup after short delay
                                setTimeout(() => {
                                    window.close();
                                }, 1000);
                            } else {
                                // Si pas de parent ou popup bloquée, rediriger dans la fenêtre actuelle
                                window.location.href = '/home';
                            }
                        } catch (error) {
                            // En cas d'erreur (cross-origin, etc.), rediriger vers /home
                            console.log('Redirecting to home due to popup error:', error);
                            window.location.href = '/home';
                        }
                    }
                    
                    // Tenter la fermeture immédiatement et aussi après un petit délai
                    // pour s'assurer que window.opener est disponible
                    closePopupAndRedirect();
                    setTimeout(closePopupAndRedirect, 100);
                </script>
            </body>
            </html>
            """, 
            athlete_name=token_data.get('athlete', {}).get('firstname', 'Utilisateur'),
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

    # === NOUVEAUX ENDPOINTS API POUR LES DONNÉES ===

    def require_auth(f):
        """Decorator to require authentication"""
        def decorated_function(*args, **kwargs):
            if not session.get('authenticated') or not session.get('auth_data'):
                return jsonify({'error': 'Authentication required'}), 401
            
            # Try to decrypt tokens to ensure they are valid
            try:
                auth_data = session.get('auth_data')
                if auth_data and 'access_token' in auth_data:
                    # Test decryption - if it fails, the session is invalid
                    security_manager.get_decrypted_tokens(auth_data)
            except Exception as e:
                print(f"Session invalid, clearing: {e}")
                session.clear()
                return jsonify({'error': 'Session invalid, please re-authenticate'}), 401
                
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    
    @app.route('/api/athlete')
    @require_auth
    def get_athlete_info():
        """Récupérer les informations de l'athlète connecté"""
        try:
            # Récupérer les tokens depuis la session sécurisée
            auth_data = session.get('auth_data')
            tokens = security_manager.get_decrypted_tokens(auth_data)
                
            # Configurer le client Strava
            strava_client.set_tokens(
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                expires_at=tokens['expires_at']
            )
            
            # Récupérer les informations de l'athlète
            athlete_info = strava_client.get_athlete()
            
            return jsonify({
                'id': athlete_info.get('id'),
                'firstname': athlete_info.get('firstname'),
                'lastname': athlete_info.get('lastname'),
                'profile': athlete_info.get('profile'),
                'profile_medium': athlete_info.get('profile_medium'),
                'city': athlete_info.get('city'),
                'country': athlete_info.get('country'),
                'sex': athlete_info.get('sex'),
                'created_at': athlete_info.get('created_at'),
                'updated_at': athlete_info.get('updated_at')
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/athlete/stats')
    @require_auth
    def get_athlete_stats():
        """Récupérer et traiter les statistiques de l'athlète"""
        try:
            # Récupérer les tokens depuis la session sécurisée
            auth_data = session.get('auth_data')
            tokens = security_manager.get_decrypted_tokens(auth_data)
                
            # Configurer le client Strava
            strava_client.set_tokens(
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                expires_at=tokens['expires_at']
            )
            
            # Récupérer les statistiques
            raw_stats = strava_client.get_athlete_stats()
            processed_stats = data_processor.process_athlete_stats(raw_stats)
            
            return jsonify(processed_stats)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/athlete/activities')
    @require_auth
    def get_athlete_activities():
        """Récupérer et traiter les activités de l'athlète"""
        try:
            # Récupérer les tokens depuis la session sécurisée
            auth_data = session.get('auth_data')
            tokens = security_manager.get_decrypted_tokens(auth_data)
                
            # Paramètres optionnels
            per_page = int(request.args.get('per_page', 30))
            page = int(request.args.get('page', 1))
            after = request.args.get('after')  # timestamp
            before = request.args.get('before')  # timestamp
            
            # Configurer le client Strava
            strava_client.set_tokens(
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                expires_at=tokens['expires_at']
            )
            
            # Récupérer les activités
            activities = strava_client.get_activities(
                per_page=per_page,
                page=page,
                after=int(after) if after else None,
                before=int(before) if before else None
            )
            
            # Formater les activités pour l'affichage avec les données brutes
            formatted_activities = []
            for activity in activities:
                formatted_activities.append({
                    'id': activity.get('id'),
                    'name': activity.get('name'),
                    'type': activity.get('type'),
                    'icon': data_processor.get_activity_icon(activity.get('type', '')),
                    # Données formatées pour l'affichage
                    'distance': data_processor.format_distance(activity.get('distance', 0)),
                    'time': data_processor.format_time(activity.get('moving_time', 0)),
                    'elevation': data_processor.format_elevation(activity.get('total_elevation_gain', 0)),
                    # Données brutes pour les calculs
                    'distance_raw': activity.get('distance', 0),
                    'moving_time': activity.get('moving_time', 0),
                    'total_elevation_gain': activity.get('total_elevation_gain', 0),
                    'date': activity.get('start_date_local'),
                    'formatted_date': data_processor.format_date(activity.get('start_date_local'))
                })
            
            return jsonify({'activities': formatted_activities})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/athlete/activities/summary')
    @require_auth
    def get_activities_summary():
        """Récupérer un résumé complet des activités"""
        try:
            # Récupérer les tokens depuis la session sécurisée
            auth_data = session.get('auth_data')
            tokens = security_manager.get_decrypted_tokens(auth_data)
            
            # Paramètres optionnels
            year = request.args.get('year')
            month = request.args.get('month')
            max_activities = request.args.get('max_activities')
            
            # Configurer le client Strava
            strava_client.set_tokens(
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                expires_at=tokens['expires_at']
            )
            
            # Récupérer les activités selon les paramètres
            if year and month:
                activities = strava_client.get_activities_by_month(int(year), int(month))
            elif year:
                activities = strava_client.get_activities_by_year(int(year))
            else:
                activities = strava_client.get_all_activities(
                    max_activities=int(max_activities) if max_activities else None
                )
            
            # Traiter les données
            summary = data_processor.process_activities_summary(activities)
            
            # Ajouter des statistiques supplémentaires
            if len(activities) > 0:
                summary['monthly_stats'] = data_processor.get_monthly_stats(activities)
                summary['weekly_stats'] = data_processor.get_weekly_stats(activities)
                summary['personal_records'] = data_processor.get_personal_records(activities)
            
            return jsonify(summary)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/athlete/activities/recent')
    @require_auth
    def get_recent_activities():
        """Récupérer les activités récentes formatées"""
        try:
            # Récupérer les tokens depuis la session sécurisée
            auth_data = session.get('auth_data')
            tokens = security_manager.get_decrypted_tokens(auth_data)
                
            count = int(request.args.get('count', 10))
            
            # Configurer le client Strava
            strava_client.set_tokens(
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                expires_at=tokens['expires_at']
            )
            
            # Récupérer les activités récentes
            activities = strava_client.get_recent_activities(count)
            
            # Les formater pour l'affichage avec les données brutes
            formatted_activities = []
            for activity in activities:
                formatted_activities.append({
                    'id': activity.get('id'),
                    'name': activity.get('name'),
                    'type': activity.get('type'),
                    'icon': data_processor.get_activity_icon(activity.get('type', '')),
                    # Données formatées pour l'affichage
                    'distance': data_processor.format_distance(activity.get('distance', 0)),
                    'time': data_processor.format_time(activity.get('moving_time', 0)),
                    'elevation': data_processor.format_elevation(activity.get('total_elevation_gain', 0)),
                    # Données brutes pour les calculs
                    'distance_raw': activity.get('distance', 0),
                    'moving_time': activity.get('moving_time', 0),
                    'total_elevation_gain': activity.get('total_elevation_gain', 0),
                    'date': activity.get('start_date_local'),
                    'formatted_date': data_processor.format_date(activity.get('start_date_local'))
                })
            
            return jsonify({'activities': formatted_activities})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/activity/<int:activity_id>/gpx')
    @require_auth
    def get_activity_gpx(activity_id):
        """Récupérer les données GPX d'une activité spécifique"""
        try:
            # Récupérer les tokens depuis la session sécurisée
            auth_data = session.get('auth_data')
            tokens = security_manager.get_decrypted_tokens(auth_data)
            
            # Configurer le client Strava
            strava_client.set_tokens(
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                expires_at=tokens['expires_at']
            )
            
            # Récupérer les données GPX
            gpx_data = strava_client.get_activity_gpx_data(activity_id)
            
            if gpx_data is None:
                return jsonify({'error': 'Aucune donnée GPS disponible pour cette activité'}), 404
            
            return jsonify({
                'activity_id': activity_id,
                'coordinates': gpx_data
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/activities/gpx')
    @require_auth 
    def get_multiple_activities_gpx():
        """Récupérer les données GPX de plusieurs activités"""
        try:
            # Récupérer les IDs des activités depuis les paramètres
            activity_ids = request.args.get('ids', '').split(',')
            activity_ids = [int(id.strip()) for id in activity_ids if id.strip().isdigit()]
            
            if not activity_ids:
                return jsonify({'error': 'Aucun ID d\'activité fourni'}), 400
            
            if len(activity_ids) > 20:  # Limiter pour éviter les abus
                return jsonify({'error': 'Maximum 20 activités par requête'}), 400
            
            # Récupérer les tokens depuis la session sécurisée
            auth_data = session.get('auth_data')
            tokens = security_manager.get_decrypted_tokens(auth_data)
            
            # Configurer le client Strava
            strava_client.set_tokens(
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                expires_at=tokens['expires_at']
            )
            
            # Récupérer les données GPX pour chaque activité
            activities_gpx = []
            print(f"🗺️ Récupération GPX: {len(activity_ids)} activités")
            
            for activity_id in activity_ids:
                try:
                    gpx_data = strava_client.get_activity_gpx_data(activity_id)
                    if gpx_data and len(gpx_data) > 0:
                        activities_gpx.append({
                            'activity_id': activity_id,
                            'coordinates': gpx_data
                        })
                except Exception as e:
                    # Continuer même si une activité échoue
                    continue
            
            print(f"📊 Au total: {len(activities_gpx)} activités avec données GPS sur {len(activity_ids)} demandées")
            
            return jsonify({
                'activities': activities_gpx,
                'total': len(activities_gpx)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/auth/logout', methods=['POST'])
    def logout():
        """Secure logout"""
        session.clear()
        return jsonify({'success': True})

    @app.route('/auth/status')
    def auth_status():
        """Check authentication status"""
        authenticated = session.get('authenticated', False)
        auth_data = session.get('auth_data')
        
        if authenticated and auth_data:
            try:
                # Verify that the session contains valid encrypted tokens
                if 'access_token' in auth_data:
                    security_manager.get_decrypted_tokens(auth_data)
                    return jsonify({'authenticated': True})
                else:
                    # No tokens in session data
                    session.clear()
                    return jsonify({'authenticated': False})
            except Exception as e:
                # Invalid session data, clear it
                print(f"Invalid session data, clearing: {e}")
                session.clear()
                return jsonify({'authenticated': False})
        else:
            return jsonify({'authenticated': False})



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