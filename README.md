# Strava Poster Builder

Application pour créer des posters personnalisés à partir de vos activités Strava.

## Configuration

1. Créez votre application Strava sur [developers.strava.com](https://developers.strava.com)
2. Copiez le fichier `.env.example` vers `.env` et configurez vos identifiants :

```bash
# Strava OAuth credentials
STRAVA_CLIENT_ID=votre_client_id_ici
STRAVA_CLIENT_SECRET=votre_client_secret_ici
STRAVA_REDIRECT_URI=http://localhost:8000/auth/callback

# Security configuration (REQUIS)
SESSION_SECRET_KEY=votre_cle_secrete_session_ici_32_caracteres_minimum
ENCRYPTION_KEY=votre_cle_chiffrement_fernet_ici_44_caracteres

# Redis (optionnel - recommandé pour la production)
REDIS_URL=redis://localhost:6379
```

### Génération des clés de sécurité

```bash
# Générer une clé de session (32 caractères minimum)
python -c "import secrets; print(secrets.token_hex(32))"

# Générer une clé de chiffrement Fernet
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Installation

```bash
# Installer les dépendances Python avec uv
uv sync
```

## Utilisation

1. **Démarrer le serveur backend OAuth :**
```bash
uv run python app.py
```

2. **Ouvrir l'interface frontend :**
Ouvrez `src/front/auth_page.html` dans votre navigateur web.

## Architecture

- **Frontend** (`src/front/auth_page.html`) : Interface utilisateur pour l'authentification
- **Backend** (`app.py`) : Application Flask principale utilisant le pattern factory
- **Routes** (`src/strava/auth_server.py`) : Serveur Flask gérant le flux OAuth de manière sécurisée

## Fonctionnalités de sécurité

- ✅ **Authentification OAuth sécurisée** avec Strava
- ✅ **Chiffrement des tokens** avec Fernet (cryptography)
- ✅ **Sessions sécurisées** avec cookies HttpOnly
- ✅ **Stockage d'état OAuth** avec Redis (fallback mémoire)
- ✅ **Protection CSRF** avec tokens de session
- ✅ **Headers de sécurité** (XSS, CSRF, HSTS)
- ✅ **Pas d'exposition des tokens** côté client
- ✅ **CORS configuré** pour les origines autorisées

## Améliorations de sécurité implémentées

### Avant (vulnérable) :
- Tokens stockés en `localStorage` (accessible via XSS)
- État OAuth en mémoire non persistant
- Transmission des tokens dans les headers personnalisés
- Pas de chiffrement des données sensibles

### Après (sécurisé) :
- Tokens chiffrés et stockés côté serveur dans des sessions
- Cookies HttpOnly sécurisés (protection XSS)
- État OAuth dans Redis avec expiration automatique
- Pas d'exposition des tokens côté client JavaScript
- Headers de sécurité et protection CSRF
