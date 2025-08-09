#!/usr/bin/env python3
"""
Security utilities for OAuth token management
"""

import os
import redis
import secrets
from cryptography.fernet import Fernet
from flask import current_app
import json
import time

class SecurityManager:
    """Manage OAuth tokens and security state securely"""
    
    def __init__(self):
        self.redis_client = None
        self.fernet = None
        self._setup_encryption()
        self._setup_redis()
    
    def _setup_encryption(self):
        """Setup encryption for sensitive data"""
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            # Generate a key if not provided (development only)
            encryption_key = Fernet.generate_key().decode()
            current_app.logger.warning("Using generated encryption key - set ENCRYPTION_KEY in production")
        
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        self.fernet = Fernet(encryption_key)
    
    def _setup_redis(self):
        """Setup Redis connection for state storage"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
        except redis.ConnectionError:
            current_app.logger.warning("Redis not available, falling back to in-memory storage")
            self.redis_client = None
    
    def store_oauth_state(self, state: str, data: dict = None) -> None:
        """Store OAuth state securely with expiration"""
        if data is None:
            data = {'timestamp': int(time.time())}
        
        if self.redis_client:
            # Store in Redis with 10 minute expiration
            self.redis_client.setex(f"oauth_state:{state}", 600, json.dumps(data))
        else:
            # Fallback: store in app context (not recommended for production)
            if not hasattr(current_app, 'oauth_states'):
                current_app.oauth_states = {}
            current_app.oauth_states[state] = data
    
    def verify_oauth_state(self, state: str) -> bool:
        """Verify OAuth state exists and remove it"""
        if self.redis_client:
            key = f"oauth_state:{state}"
            exists = self.redis_client.exists(key)
            if exists:
                self.redis_client.delete(key)
            return bool(exists)
        else:
            # Fallback
            oauth_states = getattr(current_app, 'oauth_states', {})
            return oauth_states.pop(state, None) is not None
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt token for secure storage"""
        return self.fernet.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token for use"""
        return self.fernet.decrypt(encrypted_token.encode()).decode()
    
    def create_secure_session_data(self, token_data: dict) -> dict:
        """Create encrypted session data"""
        return {
            'access_token': self.encrypt_token(token_data['access_token']),
            'refresh_token': self.encrypt_token(token_data.get('refresh_token', '')),
            'expires_at': token_data.get('expires_at'),
            'athlete_id': token_data.get('athlete', {}).get('id')
        }
    
    def get_decrypted_tokens(self, session_data: dict) -> dict:
        """Get decrypted tokens from session"""
        return {
            'access_token': self.decrypt_token(session_data['access_token']),
            'refresh_token': self.decrypt_token(session_data['refresh_token']) if session_data.get('refresh_token') else None,
            'expires_at': session_data.get('expires_at')
        }
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def cleanup_expired_states(self):
        """Clean up expired OAuth states (for fallback storage)"""
        if not self.redis_client and hasattr(current_app, 'oauth_states'):
            current_time = int(time.time())
            expired_states = []
            for state, data in current_app.oauth_states.items():
                if current_time - data.get('timestamp', 0) > 600:  # 10 minutes
                    expired_states.append(state)
            
            for state in expired_states:
                current_app.oauth_states.pop(state, None)