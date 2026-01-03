# 🚀 Mini SIEM - Démarrage Rapide (Mode Test Windows)

## ✅ L'application est démarrée !

### 🌐 Accès à l'application

- **Application Web** : http://localhost:5000
- **Page de connexion** : http://localhost:5000/login
- **Inscription** : http://localhost:5000/register
- **Dashboard** : http://localhost:5000/ (après connexion)

---

## 📝 Étapes de démarrage (FAIT ✓)

✅ L'application tourne en mode TEST avec génération d'alertes MOCK
✅ Les alertes sont générées automatiquement toutes les 5 secondes
✅ Le serveur Flask écoute sur http://localhost:5000

---

## 🔐 Créer votre compte administrateur

### Option 1 : Via l'interface web (RECOMMANDÉ)
1. Ouvrez : http://localhost:5000/register
2. Remplissez le formulaire :
   - **Nom d'utilisateur** : admin (min. 3 caractères)
   - **Email** : admin@example.com
   - **Mot de passe** : Admin123! (min. 8 caractères avec majuscules, minuscules, chiffres)
   - **Confirmer** : Admin123!
3. Cliquez sur "Créer mon compte"
4. Connectez-vous sur http://localhost:5000/login

### Option 2 : Via script (dans un nouveau terminal)
```bash
python create_admin.py
```

Ou double-cliquez sur : `create_admin.bat`

---

## 📊 Utilisation

### 1. Se connecter
- Allez sur http://localhost:5000/login
- Entrez vos identifiants
- Accédez au dashboard

### 2. Voir les alertes générées
Le générateur MOCK crée automatiquement des alertes toutes les 5 secondes :
- ✅ Alert MOCK #1: Port Scanning Detected
- ✅ Alert MOCK #2: Directory Traversal Attempt
- ✅ Alert MOCK #3: Suspicious Network Activity
- etc.

### 3. Explorer l'interface
- 🏠 **Dashboard** : Vue d'ensemble des alertes
- 🚨 **Alerts** : Liste complète des alertes
- 🔗 **Correlations** : Détection de patterns d'attaque
- 🔍 **Search** : Recherche dans les alertes
- 🚫 **Blocked IPs** : Gestion des IPs bloquées

---

## ⚡ Commandes Rapides Windows

### Démarrer l'application
```bash
python start_test.py
```
Ou double-cliquez sur : `start_test.bat`

### Créer un admin
```bash
python create_admin.py
```
Ou double-cliquez sur : `create_admin.bat`

### Arrêter l'application
Appuyez sur `Ctrl + C` dans le terminal

---

## 📈 Statistiques en temps réel

L'application génère actuellement :
- **Alertes MOCK** : 1-3 alertes toutes les 5 secondes
- **Types d'alertes** : Port Scanning, SQL Injection, Brute Force, DNS queries, etc.
- **Enrichissement IP** : Géolocalisation automatique
- **Corrélations** : Détection automatique de patterns

---

## 🐛 Dépannage

### Port 5000 déjà utilisé ?
Modifiez dans `start_test.py` :
```python
app.run(host='0.0.0.0', port=8080)  # Changez le port
```

### Erreur de module manquant ?
```bash
pip install -r requirements.txt
```

### Pas d'alertes générées ?
Vérifiez les logs dans le terminal. Le générateur MOCK devrait afficher :
```
✅ Alert MOCK #X: [Type d'alerte] from [IP]
```

---

## 📁 Structure des fichiers

```
mini_siem/
├── start_test.py          ← Script de démarrage mode TEST
├── start_test.bat         ← Script batch Windows
├── create_admin.py        ← Créer un administrateur
├── create_admin.bat       ← Script batch pour admin
├── app/
│   ├── main.py           ← Application Flask
│   └── templates/        ← Templates HTML
│       ├── login.html    ← Page de connexion
│       ├── register.html ← Page d'inscription
│       └── dashboard.html
├── core/
│   ├── database.py       ← Gestion base de données
│   ├── collector.py      ← Collecteur + Mock
│   └── enricher.py       ← Enrichissement IP
└── data/
    └── siem.db          ← Base de données SQLite
```

---

## 🎯 Prochaines étapes

1. ✅ Créez votre compte admin
2. ✅ Connectez-vous
3. ✅ Explorez le dashboard
4. ✅ Consultez les alertes en temps réel
5. ✅ Testez les fonctionnalités (recherche, blocage IP, etc.)

---

## 💡 Astuces

- **Générer plus d'alertes** : Modifiez `MOCK_ALERT_INTERVAL = 2` dans `config.py`
- **Changer les types d'alertes** : Voir `MockAlertGenerator` dans `core/collector.py`
- **Base de données** : Fichier SQLite dans `data/siem.db`
- **Logs** : Tous les événements sont affichés dans le terminal

---

## 🔄 Redémarrage

Pour redémarrer l'application :
1. `Ctrl + C` dans le terminal
2. Relancer : `python start_test.py` ou `start_test.bat`

---

**Bon test ! 🛡️**

Consultez `AUTH_README.md` pour plus d'informations sur l'authentification.
