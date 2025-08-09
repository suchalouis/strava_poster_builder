# Strava Poster Builder

Application pour créer des posters personnalisés à partir de vos activités Strava.

## Configuration

1. Créez votre application Strava sur [developers.strava.com](https://developers.strava.com)
2. Copiez le fichier `.env` et ajoutez vos identifiants :

```bash
# Strava OAuth credentials
STRAVA_CLIENT_ID=votre_client_id_ici
STRAVA_CLIENT_SECRET=votre_client_secret_ici
STRAVA_REDIRECT_URI=http://localhost:8000/auth/callback
```

## Installation

```bash
# Installer les dépendances Python
pip install -r requirements.txt
```

## Utilisation

1. **Démarrer le serveur backend OAuth :**
```bash
python src/strava/auth_server.py
```

2. **Ouvrir l'interface frontend :**
Ouvrez `src/front/auth_page.html` dans votre navigateur web.

## Architecture

- **Frontend** (`src/front/auth_page.html`) : Interface utilisateur pour l'authentification
- **Backend** (`src/strava/auth_server.py`) : Serveur Flask gérant le flux OAuth de manière sécurisée

## Fonctionnalités

- Authentification OAuth sécurisée avec Strava
- Gestion des tokens d'accès et de rafraîchissement
- Interface utilisateur responsive
- Stockage local des tokens pour la persistance de session
