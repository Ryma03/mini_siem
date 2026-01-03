# 🔐 Système d'Authentification - Mini SIEM

## Vue d'ensemble

Le système d'authentification a été ajouté pour sécuriser l'accès au dashboard Mini SIEM. Seuls les administrateurs authentifiés peuvent accéder aux fonctionnalités de surveillance et de gestion.

## Fonctionnalités

### ✅ Implémentées

- **Page de Connexion** (`/login`)
  - Authentification par nom d'utilisateur et mot de passe
  - Option "Se souvenir de moi" (session de 24h)
  - Messages d'erreur conviviaux
  - Design moderne et responsive

- **Page d'Inscription** (`/register`)
  - Création de nouveaux comptes administrateurs
  - Validation des données (email, nom d'utilisateur, mot de passe)
  - Vérification de la force du mot de passe
  - Indicateur visuel de force du mot de passe
  - Confirmation du mot de passe

- **Déconnexion** (`/logout`)
  - Bouton accessible depuis toutes les pages
  - Nettoyage complet de la session

- **Protection des Routes**
  - Toutes les pages sensibles sont protégées
  - Redirection automatique vers la page de login si non authentifié
  - Dashboard, Alertes, Corrélations, Recherche, IPs bloquées

- **Gestion des Sessions**
  - Sessions sécurisées avec Flask
  - Durée de session configurable
  - Support "Remember me"

## Installation et Configuration

### 1. Vérifier les dépendances

Toutes les dépendances nécessaires sont déjà dans `requirements.txt`:
```bash
flask==2.3.3
requests==2.31.0
ipwhois==1.2.0
Werkzeug==2.3.7
```

### 2. Créer le premier administrateur

Deux méthodes sont disponibles :

#### Méthode A : Script interactif (Recommandé)
```bash
python create_admin.py
```

Le script vous guidera pour créer votre premier compte administrateur.

#### Méthode B : Via l'interface web
1. Démarrez l'application : `python app/main.py`
2. Ouvrez votre navigateur : `http://localhost:5000/register`
3. Remplissez le formulaire d'inscription

### 3. Se connecter

1. Allez sur `http://localhost:5000/login`
2. Entrez vos identifiants
3. Accédez au dashboard sécurisé

## Structure de la Base de Données

Une nouvelle table `admin_users` a été ajoutée :

```sql
CREATE TABLE admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);
```

## Sécurité

### Mots de passe
- **Hachage sécurisé** : Utilisation de Werkzeug PBKDF2 SHA-256
- **Validation stricte** :
  - Minimum 8 caractères
  - Au moins une majuscule
  - Au moins une minuscule
  - Au moins un chiffre

### Sessions
- **Secret key** : Configurable via variable d'environnement `SECRET_KEY`
- **Durée** : 24h par défaut avec l'option "Se souvenir"
- **Cookies sécurisés** : Support HTTPS ready

### Protection CSRF
Pour production, il est recommandé d'ajouter Flask-WTF pour la protection CSRF.

## Configuration Production

### Variables d'environnement recommandées

```bash
# Secret key pour les sessions (IMPORTANT!)
export SECRET_KEY='votre-cle-secrete-tres-longue-et-aleatoire'

# Base de données
export DATABASE_PATH='/var/lib/mini_siem/siem.db'

# Web server
export WEB_HOST='0.0.0.0'
export WEB_PORT='5000'
```

### Recommandations de sécurité

1. **Changez la secret key** en production :
   ```python
   app.secret_key = os.environ.get('SECRET_KEY', 'CHANGE-THIS-IN-PRODUCTION')
   ```

2. **Utilisez HTTPS** avec un reverse proxy (nginx, Apache)

3. **Limitez les tentatives de connexion** (à implémenter si besoin)

4. **Sauvegardez régulièrement** la base de données

5. **Logs d'authentification** : Tous les événements sont loggés

## API et Authentification

Toutes les routes API nécessitent maintenant une authentification :

- ✅ `/api/alerts`
- ✅ `/api/alerts/ip/<ip>`
- ✅ `/api/correlations`
- ✅ `/api/enrich-ip/<ip>`
- ✅ `/api/stats`
- ✅ `/api/block-ip`
- ✅ `/api/unblock-ip`
- ✅ `/api/blocked-ips`

Pour utiliser l'API, vous devez être authentifié via session cookie.

## Fichiers Modifiés/Créés

### Nouveaux fichiers
- `app/templates/login.html` - Page de connexion
- `app/templates/register.html` - Page d'inscription
- `create_admin.py` - Script de création d'admin
- `AUTH_README.md` - Cette documentation

### Fichiers modifiés
- `core/database.py` - Ajout méthodes gestion utilisateurs
- `app/main.py` - Ajout routes auth + décorateur login_required
- `app/templates/dashboard.html` - Ajout bouton déconnexion

## Utilisation

### Créer un administrateur supplémentaire

```bash
python create_admin.py
```

### Accéder au système

1. **Login** : `http://localhost:5000/login`
2. **Dashboard** : `http://localhost:5000/` (redirige vers login si non authentifié)
3. **Logout** : Cliquez sur "Déconnexion" dans le header

### Réinitialiser un mot de passe (via base de données)

```python
from werkzeug.security import generate_password_hash
from core.database import DatabaseManager

db = DatabaseManager()
new_password_hash = generate_password_hash('nouveau_mot_de_passe')

# Manuellement dans SQLite
# UPDATE admin_users SET password_hash = 'hash' WHERE username = 'admin';
```

## Dépannage

### Problème : "Aucun module nommé werkzeug"
```bash
pip install -r requirements.txt
```

### Problème : "Table admin_users n'existe pas"
La table est créée automatiquement au démarrage. Redémarrez l'application.

### Problème : "Nom d'utilisateur ou mot de passe incorrect"
- Vérifiez vos identifiants
- Créez un nouvel administrateur avec `create_admin.py`
- Consultez les logs : `mini_siem.log`

### Problème : Session expire trop rapidement
Modifiez dans `app/main.py`:
```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=48)  # 48h au lieu de 24h
```

## Support

Pour toute question ou problème :
1. Consultez les logs : `mini_siem.log`
2. Vérifiez la base de données : `data/siem.db`
3. Consultez la documentation principale : `README.md`

## Prochaines Améliorations Possibles

- [ ] Limitation des tentatives de connexion (rate limiting)
- [ ] Réinitialisation de mot de passe par email
- [ ] Authentification à deux facteurs (2FA)
- [ ] Gestion des rôles (admin, viewer, analyst)
- [ ] Journal d'audit des connexions
- [ ] API tokens pour accès programmatique
- [ ] OAuth/SAML pour SSO enterprise

---

**Version** : 1.0  
**Date** : Janvier 2026  
**Auteur** : Mini SIEM Project
