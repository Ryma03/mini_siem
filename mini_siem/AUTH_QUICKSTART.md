# 🚀 Guide de Démarrage Rapide - Système d'Authentification

## Étape 1 : Installation des dépendances

```bash
pip install -r requirements.txt
```

## Étape 2 : Créer votre premier administrateur

```bash
python create_admin.py
```

Suivez les instructions à l'écran :
- Entrez un nom d'utilisateur (min. 3 caractères)
- Entrez un email valide
- Créez un mot de passe fort (min. 8 caractères, avec majuscules, minuscules et chiffres)
- Confirmez le mot de passe

Exemple :
```
===========================================================
  Création du premier administrateur - Mini SIEM
===========================================================

Nom d'utilisateur: admin
Email: admin@example.com
Mot de passe: ********
Confirmer le mot de passe: ********

Création de l'utilisateur administrateur...

===========================================================
✅ Administrateur créé avec succès !
===========================================================
Nom d'utilisateur: admin
Email: admin@example.com

Vous pouvez maintenant vous connecter à: http://localhost:5000/login
===========================================================
```

## Étape 3 : Démarrer l'application

```bash
python app/main.py
```

L'application démarre sur `http://localhost:5000`

## Étape 4 : Se connecter

1. Ouvrez votre navigateur : `http://localhost:5000`
2. Vous serez automatiquement redirigé vers `/login`
3. Entrez vos identifiants
4. Accédez au dashboard sécurisé !

## Utilisation

### Créer des administrateurs supplémentaires

Deux options :
1. Via le script : `python create_admin.py`
2. Via l'interface web : `http://localhost:5000/register`

### Se déconnecter

Cliquez sur le bouton "Déconnexion" en haut à droite du dashboard.

### Accès aux différentes pages

Toutes ces pages nécessitent maintenant une authentification :
- 🏠 Dashboard : `/`
- 🚨 Alertes : `/alerts`
- 🔗 Corrélations : `/correlations`
- 🔍 Recherche : `/search`
- 🚫 IPs Bloquées : `/blocked-ips`

## Configuration (Optionnel)

### Changer la clé secrète

Pour la production, définissez une clé secrète :

**Windows (PowerShell):**
```powershell
$env:SECRET_KEY = "votre-cle-secrete-tres-longue-aleatoire-unique"
python app/main.py
```

**Linux/Mac:**
```bash
export SECRET_KEY="votre-cle-secrete-tres-longue-aleatoire-unique"
python app/main.py
```

### Changer la durée de session

Modifiez dans `app/main.py` :
```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Changez le nombre d'heures
```

## Résolution de problèmes

### "Table admin_users n'existe pas"
La table est créée automatiquement. Si le problème persiste :
1. Supprimez `data/siem.db`
2. Redémarrez l'application
3. Recréez l'administrateur avec `python create_admin.py`

### "Module 'werkzeug' not found"
```bash
pip install werkzeug
```

### Mot de passe oublié
Utilisez le script pour créer un nouvel administrateur ou consultez AUTH_README.md pour la réinitialisation manuelle.

## Fonctionnalités de sécurité

✅ Mots de passe hachés (PBKDF2 SHA-256)  
✅ Validation stricte des mots de passe  
✅ Sessions sécurisées  
✅ Protection de toutes les routes  
✅ Logs d'authentification  
✅ Support "Remember me"  

## Prochaines étapes

Consultez `AUTH_README.md` pour :
- Configuration avancée
- Recommandations de sécurité en production
- API et authentification
- Dépannage détaillé

---

**Besoin d'aide ?** Consultez les logs : `mini_siem.log`
