"""
Flask web interface for Mini SIEM
Provides dashboard for visualizing and managing alerts
"""

from flask import Flask, render_template, jsonify, request
import logging
from datetime import datetime, timedelta
import json
from pathlib import Path

# Get parent directory for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import DatabaseManager
from core.enricher import IPEnricher

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize managers
db_manager = DatabaseManager()
ip_enricher = IPEnricher(use_free_api=True)


@app.route('/')
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
def alerts_page():
    """Alerts management page"""
    try:
        alerts = db_manager.get_recent_alerts(limit=100)
        return render_template('alerts.html', alerts=alerts)

    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/correlations')
def correlations_page():
    """Correlations page"""
    try:
        correlations = db_manager.get_correlations(limit=50)
        return render_template('correlations.html', correlations=correlations)

    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/search')
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
