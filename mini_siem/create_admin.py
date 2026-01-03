#!/usr/bin/env python3
"""
Script pour créer un premier utilisateur administrateur
"""

import sys
from pathlib import Path
from werkzeug.security import generate_password_hash
import getpass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import DatabaseManager

def create_first_admin():
    """Créer le premier utilisateur administrateur"""
    
    print("=" * 60)
    print("  Création du premier administrateur - Mini SIEM")
    print("=" * 60)
    print()
    
    db_manager = DatabaseManager()
    
    # Get user input
    username = input("Nom d'utilisateur: ").strip()
    if len(username) < 3:
        print("❌ Le nom d'utilisateur doit contenir au moins 3 caractères")
        return False
    
    email = input("Email: ").strip()
    if '@' not in email:
        print("❌ Email invalide")
        return False
    
    while True:
        password = getpass.getpass("Mot de passe: ")
        if len(password) < 8:
            print("❌ Le mot de passe doit contenir au moins 8 caractères")
            continue
            
        if not any(c.isupper() for c in password):
            print("❌ Le mot de passe doit contenir au moins une majuscule")
            continue
            
        if not any(c.islower() for c in password):
            print("❌ Le mot de passe doit contenir au moins une minuscule")
            continue
            
        if not any(c.isdigit() for c in password):
            print("❌ Le mot de passe doit contenir au moins un chiffre")
            continue
        
        confirm = getpass.getpass("Confirmer le mot de passe: ")
        if password != confirm:
            print("❌ Les mots de passe ne correspondent pas")
            continue
            
        break
    
    # Hash password
    password_hash = generate_password_hash(password)
    
    # Create admin
    print()
    print("Création de l'utilisateur administrateur...")
    success = db_manager.create_admin(username, password_hash, email)
    
    if success:
        print()
        print("=" * 60)
        print("✅ Administrateur créé avec succès !")
        print("=" * 60)
        print(f"Nom d'utilisateur: {username}")
        print(f"Email: {email}")
        print()
        print("Vous pouvez maintenant vous connecter à: http://localhost:5000/login")
        print("=" * 60)
        return True
    else:
        print()
        print("❌ Erreur: Ce nom d'utilisateur ou email existe déjà")
        return False

if __name__ == '__main__':
    try:
        create_first_admin()
    except KeyboardInterrupt:
        print("\n\n⚠️  Opération annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        sys.exit(1)
