"""
Flask web interface for Mini SIEM
Provides dashboard for visualizing and managing alerts
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import logging
from datetime import datetime, timedelta
import json
from pathlib import Path
import threading
import time
import os

# Get parent directory for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import DatabaseManager
from core.enricher import IPEnricher
from core.collector import AlertCollector
import config

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'mini-siem-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Initialize managers
db_manager = DatabaseManager()
ip_enricher = IPEnricher(use_free_api=True)

# Initialize real Snort collector
alert_collector = AlertCollector(alert_file=config.SNORT_ALERT_FILE)

# Start collector thread
def start_collector():
    """Start the alert collector in background"""
    if alert_collector.start_collection():
        logger.info("Real Snort alert collector started successfully")
        while True:
            try:
                alerts = alert_collector.read_new_alerts()
                if alerts:
                    for alert in alerts:
                        # Enrich and store alerts
                        enriched_alert = ip_enricher.enrich_alert(alert)
                        db_manager.insert_alert(enriched_alert)
                        logger.info(f"Snort Alert collected: {alert['signature']}")
                time.sleep(config.COLLECTION_INTERVAL)
            except Exception as e:
                logger.error(f"Error in collector loop: {str(e)}")
                time.sleep(5)
    else:
        logger.warning("Could not start real Snort collector - file not found")

# Start collector thread on app startup
collector_thread = threading.Thread(target=start_collector, daemon=True)
collector_thread.start()


# Authentication decorator
def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        # Validate input
        if not username or not password:
            return render_template('login.html', error='Veuillez remplir tous les champs')
        
        # Get user from database
        user = db_manager.get_admin_by_username(username)
        
        if user and check_password_hash(user['password_hash'], password):
            # Login successful
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            
            if remember:
                session.permanent = True
            
            # Update last login
            db_manager.update_last_login(username)
            
            logger.info(f"User {username} logged in successfully")
            flash('Connexion réussie !', 'success')
            return redirect(url_for('index'))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template('login.html', error='Nom d\'utilisateur ou mot de passe incorrect')
    
    # GET request - show login form
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page and handler"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password or not confirm_password:
            return render_template('register.html', error='Veuillez remplir tous les champs')
        
        if len(username) < 3:
            return render_template('register.html', error='Le nom d\'utilisateur doit contenir au moins 3 caractères')
        
        if len(password) < 8:
            return render_template('register.html', error='Le mot de passe doit contenir au moins 8 caractères')
        
        if password != confirm_password:
            return render_template('register.html', error='Les mots de passe ne correspondent pas')
        
        # Check password strength
        if not any(c.isupper() for c in password) or not any(c.islower() for c in password) or not any(c.isdigit() for c in password):
            return render_template('register.html', error='Le mot de passe doit contenir des majuscules, minuscules et chiffres')
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create user
        success = db_manager.create_admin(username, password_hash, email)
        
        if success:
            logger.info(f"New admin user registered: {username}")
            return render_template('login.html', success='Compte créé avec succès ! Vous pouvez maintenant vous connecter.')
        else:
            return render_template('register.html', error='Ce nom d\'utilisateur ou email existe déjà')
    
    # GET request - show registration form
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    """Logout handler"""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"User {username} logged out")
    flash('Déconnexion réussie !', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    try:
        # Get statistics
        stats = db_manager.get_alert_stats()
        recent_alerts = db_manager.get_recent_alerts(limit=50)
        correlations = db_manager.get_correlations(limit=10)

        # Calculate additional stats
        high_severity = sum(1 for a in recent_alerts if a['severity'] == 'HIGH')
        critical_severity = sum(1 for a in recent_alerts if a['severity'] == 'CRITICAL')

        return render_template('dashboard.html',
                             stats=stats,
                             alerts=recent_alerts,
                             correlations=correlations,
                             high_count=high_severity,
                             critical_count=critical_severity,
                             last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        return render_template('error.html', error=str(e)), 500


@app.route('/api/alerts', methods=['GET'])
@login_required
def get_alerts():
    """Get recent alerts as JSON"""
    try:
        limit = request.args.get('limit', 50, type=int)
        alerts = db_manager.get_recent_alerts(limit=limit)

        return jsonify({
            'success': True,
            'count': len(alerts),
            'alerts': alerts
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alerts/ip/<ip>', methods=['GET'])
@login_required
def get_alerts_by_ip(ip):
    """Get alerts from specific IP"""
    try:
        minutes = request.args.get('minutes', 10, type=int)
        alerts = db_manager.get_alerts_by_ip(ip, minutes=minutes)

        return jsonify({
            'success': True,
            'ip': ip,
            'count': len(alerts),
            'time_window_minutes': minutes,
            'alerts': alerts
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/correlations', methods=['GET'])
@login_required
def get_correlations():
    """Get detected correlations"""
    try:
        correlations = db_manager.get_correlations(limit=20)

        return jsonify({
            'success': True,
            'count': len(correlations),
            'correlations': correlations
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/enrich-ip/<ip>', methods=['GET'])
@login_required
def enrich_ip(ip):
    """Enrich an IP address"""
    try:
        enrichment = ip_enricher.enrich_ip(ip)

        return jsonify({
            'success': True,
            'ip': ip,
            'enrichment': enrichment
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Get system statistics"""
    try:
        stats = db_manager.get_alert_stats()
        
        # Get alerts from last hour
        alerts_last_hour = len(db_manager.get_recent_alerts(limit=10000))
        
        return jsonify({
            'success': True,
            'stats': {
                **stats,
                'alerts_last_hour': min(alerts_last_hour, 10000)
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alerts/severity/<severity>', methods=['GET'])
@login_required
def get_alerts_by_severity(severity):
    """Get alerts by severity level"""
    try:
        all_alerts = db_manager.get_recent_alerts(limit=200)
        filtered = [a for a in all_alerts if a['severity'] == severity.upper()]

        return jsonify({
            'success': True,
            'severity': severity,
            'count': len(filtered),
            'alerts': filtered
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/alerts')
@login_required
def alerts_page():
    """Alerts management page"""
    try:
        alerts = db_manager.get_recent_alerts(limit=100)
        return render_template('alerts.html', alerts=alerts)

    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/correlations')
@login_required
def correlations_page():
    """Correlations page"""
    try:
        correlations = db_manager.get_correlations(limit=50)
        return render_template('correlations.html', correlations=correlations)

    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/search')
@login_required
def search():
    """Search alerts"""
    try:
        query = request.args.get('q', '')
        query_type = request.args.get('type', 'ip')  # ip, signature, severity

        all_alerts = db_manager.get_recent_alerts(limit=500)
        results = []

        if query_type == 'ip':
            results = [a for a in all_alerts if query in a['src_ip'] or query in a['dst_ip']]
        elif query_type == 'signature':
            results = [a for a in all_alerts if query.lower() in a['signature'].lower()]
        elif query_type == 'severity':
            results = [a for a in all_alerts if a['severity'].upper() == query.upper()]

        return render_template('search.html', 
                             results=results, 
                             query=query, 
                             query_type=query_type)

    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/api/block-ip', methods=['POST'])
@login_required
def block_ip_api():
    """Block an IP address"""
    try:
        data = request.get_json()
        ip_address = data.get('ip')
        reason = data.get('reason', 'Blocked via web interface')
        
        if not ip_address:
            return jsonify({'success': False, 'message': 'IP address required'}), 400
        
        success = db_manager.block_ip(ip_address, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'IP {ip_address} has been blocked',
                'ip': ip_address
            })
        else:
            return jsonify({
                'success': False,
                'message': f'IP {ip_address} is already blocked'
            }), 409
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/unblock-ip', methods=['POST'])
@login_required
def unblock_ip_api():
    """Unblock an IP address"""
    try:
        data = request.get_json()
        ip_address = data.get('ip')
        
        if not ip_address:
            return jsonify({'success': False, 'message': 'IP address required'}), 400
        
        success = db_manager.unblock_ip(ip_address)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'IP {ip_address} has been unblocked',
                'ip': ip_address
            })
        else:
            return jsonify({
                'success': False,
                'message': f'IP {ip_address} was not blocked'
            }), 404
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/blocked-ips')
@login_required
def get_blocked_ips_api():
    """Get list of all blocked IPs"""
    try:
        blocked = db_manager.get_blocked_ips()
        return jsonify({
            'success': True,
            'count': len(blocked),
            'blocked_ips': blocked
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/blocked-ips')
@login_required
def blocked_ips_page():
    """Show blocked IPs management page"""
    try:
        blocked = db_manager.get_blocked_ips()
        return render_template('blocked_ips.html', blocked_ips=blocked)
    
    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', error='Page not found'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('error.html', error='Internal server error'), 500


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
