# Strava Poster API

API FastAPI moderne pour générer des posters personnalisés à partir des données Strava.

## 🏗️ Architecture

Ce projet utilise une architecture modulaire FastAPI avec séparation claire des responsabilités :

```
project-strava-api/
├── app/                    # Configuration application
├── strava/                 # Module Strava (API client)
├── poster/                 # Module génération poster  
├── routers/               # Routes API FastAPI
├── core/                  # Infrastructure (DB, sécurité)
├── models/                # Modèles SQLAlchemy
├── services/              # Logique métier
├── schemas/               # Schémas Pydantic
└── tests/                 # Tests unitaires
```

## 🚀 Fonctionnalités

### Authentification OAuth Strava
- ✅ Connexion via OAuth Strava 
- ✅ Gestion automatique du refresh des tokens
- ✅ Sessions sécurisées avec JWT
- ✅ Protection CSRF

### API Strava
- ✅ Client Strava unifié avec rate limiting
- ✅ Récupération des activités avec pagination
- ✅ Données GPS et streams détaillés
- ✅ Statistiques d'athlète complètes
- ✅ Gestion d'erreurs robuste

### Génération de Posters
- 🔄 Templates multiples (Classic, Modern, Minimalist)
- 🔄 Formats multiples (PDF, PNG, JPEG)
- 🔄 Personnalisation avancée (couleurs, contenu)
- 🔄 Génération async avec file d'attente

### Stockage & Sécurité
- ✅ Stockage en mémoire (aucune BDD requise)
- ✅ Sessions utilisateur temporaires
- ✅ Authentification JWT sécurisée
- ⚠️ Données perdues au redémarrage

## ⚙️ Installation

### Prérequis
- Python 3.11+

### Configuration

1. **Cloner et installer les dépendances**
```bash
git clone <repository>
cd project-strava-api
pip install -r requirements.txt
```

2. **Configuration des variables d'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos valeurs
```

Variables requises :
```env
STRAVA_CLIENT_ID=your_strava_client_id
STRAVA_CLIENT_SECRET=your_strava_client_secret
SECRET_KEY=your-super-secret-key
```

### Développement

```bash
# Lancer le serveur de développement
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Tests
pytest

# Linting
black . && isort . && flake8
```

## 📖 API Documentation

Une fois l'application lancée, la documentation interactive est disponible :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Endpoints principaux

#### Authentification
```
POST   /api/v1/auth/login          # Initier OAuth Strava
GET    /api/v1/auth/callback       # Callback OAuth
POST   /api/v1/auth/refresh        # Refresh token
POST   /api/v1/auth/logout         # Déconnexion
```

#### Athlète
```
GET    /api/v1/athlete/profile     # Profil athlète
GET    /api/v1/athlete/stats       # Statistiques globales
```

#### Activités
```
GET    /api/v1/activities/         # Liste des activités
GET    /api/v1/activities/{id}     # Détail d'une activité
GET    /api/v1/activities/summary  # Résumé avec stats
GET    /api/v1/activities/gpx      # Données GPS multiples
```

#### Posters
```
GET    /api/v1/poster/configs      # Configurations
POST   /api/v1/poster/configs      # Créer configuration
POST   /api/v1/poster/generate     # Générer poster
GET    /api/v1/poster/history      # Historique
```

## 🔒 Sécurité

### Authentification
- **OAuth 2.0** avec Strava comme provider
- **JWT tokens** pour l'authentification API
- **Sessions sécurisées** avec tokens chiffrés
- **CSRF protection** sur les flux OAuth

### Stockage
- **Tokens Strava chiffrés** en base de données
- **Mots de passe hashés** avec bcrypt
- **Sessions limitées dans le temps**

### API
- **Rate limiting** respectant les limites Strava
- **Headers de sécurité** automatiques
- **Validation stricte** avec Pydantic
- **Logs d'audit** complets

## 🏃‍♂️ Scripts de Développement

```bash
# Générer les migrations
alembic revision --autogenerate -m "Description"

# Nettoyer les données expirées
python -m scripts.cleanup_expired_data

# Import/Export configurations
python -m scripts.manage_configs --export
python -m scripts.manage_configs --import config.json
```

## 📊 Monitoring

### Logs
Les logs sont structurés avec différents niveaux :
- **INFO** : Opérations normales
- **WARNING** : Problèmes non critiques  
- **ERROR** : Erreurs nécessitant attention

### Métriques
- Temps de réponse API
- Utilisation des limites Strava
- Taux de succès/échec des générations
- Statistiques d'utilisation

## 🤝 Contribution

1. Fork du projet
2. Créer une branche feature (`git checkout -b feature/amazing-feature`)
3. Commit des changements (`git commit -m 'Add amazing feature'`)
4. Push vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

### Standards de code
- **Type hints** obligatoires
- **Docstrings** pour les fonctions publiques
- **Tests unitaires** pour les nouvelles fonctionnalités
- **PEP 8** avec Black formatter

## 📝 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour les détails.

## 🔗 Liens utiles

- [Documentation Strava API](https://developers.strava.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)