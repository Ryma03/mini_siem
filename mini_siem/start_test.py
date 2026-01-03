"""
Script de démarrage rapide pour Mini SIEM en mode TEST (Windows)
Génère des alertes mock pour tester l'application sans Snort
"""

import sys
import os
import threading
import time
import logging
from pathlib import Path

# Setup Python path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask
from core.database import DatabaseManager
from core.enricher import IPEnricher
from core.collector import MockAlertGenerator
import config

# Import Flask app from main.py
from app.main import app, db_manager, ip_enricher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_mock_alerts():
    """Background thread to generate mock alerts continuously"""
    logger.info("🚀 Démarrage du générateur d'alertes MOCK...")
    
    alert_count = 0
    
    while True:
        try:
            # Generate 1-3 random alerts
            import random
            count = random.randint(1, 3)
            alerts = MockAlertGenerator.generate_batch(count=count)
            
            for alert in alerts:
                # Enrich and store
                enriched_alert = ip_enricher.enrich_alert(alert)
                db_manager.insert_alert(enriched_alert)
                alert_count += 1
                logger.info(f"✅ Alert MOCK #{alert_count}: {alert['signature']} from {alert['src_ip']}")
            
            # Wait before generating more alerts
            time.sleep(config.MOCK_ALERT_INTERVAL)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération d'alertes mock: {str(e)}")
            time.sleep(5)


def print_banner():
    """Print startup banner"""
    print("\n" + "=" * 70)
    print("  🛡️  MINI SIEM - MODE TEST (Alertes Mock)")
    print("=" * 70)
    print()
    print("  📍 Application Web : http://localhost:5000")
    print("  🔐 Connexion       : http://localhost:5000/login")
    print("  📊 Dashboard       : http://localhost:5000/")
    print()
    print("  ⚡ Génération automatique d'alertes mock toutes les", config.MOCK_ALERT_INTERVAL, "secondes")
    print("  🗄️  Base de données : data/siem.db")
    print()
    print("=" * 70)
    print("\n✨ Pour créer un compte admin, exécutez: python create_admin.py")
    print("⚠️  Appuyez sur Ctrl+C pour arrêter l'application\n")


def check_admin_exists():
    """Check if at least one admin user exists"""
    try:
        # Try to check if we have any admin
        import sqlite3
        db_path = Path(__file__).parent / "data" / "siem.db"
        
        if not db_path.exists():
            return False
            
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM admin_users")
            count = cursor.fetchone()[0]
            return count > 0
    except:
        return False


if __name__ == '__main__':
    try:
        # Print banner
        print_banner()
        
        # Check for admin users
        if not check_admin_exists():
            print("⚠️  ATTENTION: Aucun administrateur détecté!")
            print("   Créez un compte admin avec: python create_admin.py")
            print("   Ou allez sur: http://localhost:5000/register\n")
        
        # Start mock alert generator in background
        mock_thread = threading.Thread(target=generate_mock_alerts, daemon=True)
        mock_thread.start()
        
        logger.info("🌐 Démarrage du serveur Flask...")
        
        # Start Flask app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Arrêt de l'application...")
        print("👋 Au revoir!\n")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
