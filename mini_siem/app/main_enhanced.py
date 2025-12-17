"""
Flask web interface for Mini SIEM - Enhanced Version
Provides real-time dashboard, analytics, and advanced search
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
from datetime import datetime, timedelta
import json
from pathlib import Path
import plotly
import plotly.graph_objects as go
import pandas as pd
from collections import Counter
import threading
import time

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
app.config['SECRET_KEY'] = 'mini-siem-secret-key-2025'

# Initialize Socket.IO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

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
                        alert_id = db_manager.insert_alert(enriched_alert)
                        logger.info(f"Snort Alert collected: {alert['signature']} [ID: {alert_id}]")
                        # Emit real-time update via WebSocket
                        socketio.emit('new_alert', enriched_alert, broadcast=True)
                time.sleep(config.COLLECTION_INTERVAL)
            except Exception as e:
                logger.error(f"Error in collector loop: {str(e)}")
                time.sleep(5)
    else:
        logger.warning("Could not start real Snort collector - file not found")

# Start collector thread on app startup
collector_thread = threading.Thread(target=start_collector, daemon=True)
collector_thread.start()

# Shared color palette for charts (consistent across charts)
PALETTE = {
    'severity': {
        'CRITICAL': '#e74c3c',
        'HIGH': '#ff8c42',
        'MEDIUM': '#3498db',
        'LOW': '#2ecc71',
        'INFO': '#95a5a6'
    },
    'accent': '#6c5ce7',
    'bars': ['#6c5ce7', '#00b894', '#e17055', '#fdcb6e', '#0984e3']
}


# ==================== WebSocket Events ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected to WebSocket')
    emit('response', {'data': 'Connected to Mini SIEM'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected from WebSocket')


@socketio.on('subscribe_alerts')
def handle_subscribe_alerts():
    """Subscribe to real-time alerts"""
    join_room('alerts')
    emit('response', {'data': 'Subscribed to alerts'})


def broadcast_new_alert(alert):
    """Broadcast new alert to all connected clients"""
    try:
        socketio.emit('new_alert', {
            'id': alert.get('id'),
            'timestamp': alert.get('timestamp'),
            'signature': alert.get('signature'),
            'src_ip': alert.get('src_ip'),
            'severity': alert.get('severity')
        }, room='alerts')
    except Exception as e:
        logger.error(f"Error broadcasting alert: {e}")


# ==================== Chart Generation ====================

def generate_alerts_timeline_chart(days=7):
    """Generate alerts timeline chart (last N days)"""
    try:
        alerts = db_manager.get_recent_alerts(limit=1000)
        
        # Convert to DataFrame
        df = pd.DataFrame(alerts)
        if df.empty:
            return None
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        # Count alerts per day
        daily_counts = df.groupby('date').size()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_counts.index.astype(str),
            y=daily_counts.values,
            mode='lines+markers',
            name='Alerts',
            line=dict(color=PALETTE['accent'], width=3),
            marker=dict(size=8, color=PALETTE['accent'])
        ))
        
        fig.update_layout(
            title='Alert Timeline (Last 7 Days)',
            xaxis_title='Date',
            yaxis_title='Alert Count',
            hovermode='x unified',
            template='plotly_dark',
            height=520,
            font=dict(family='Segoe UI, Arial, sans-serif', size=14, color='#f8f9fa'),
            xaxis=dict(tickfont=dict(size=12, color='#f8f9fa'), title=dict(text='Date', font=dict(size=13, color='#f8f9fa'))),
            yaxis=dict(tickfont=dict(size=12, color='#f8f9fa'), title=dict(text='Alert Count', font=dict(size=13, color='#f8f9fa')), dtick=1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        logger.error(f"Error generating timeline chart: {e}")
        return None


def generate_severity_chart():
    """Generate severity distribution chart"""
    try:
        alerts = db_manager.get_recent_alerts(limit=1000)
        
        if not alerts:
            return None
        
        severity_counts = Counter(a['severity'] for a in alerts)

        # Ensure a deterministic order for common severities
        ordered_levels = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
        labels = [lvl for lvl in ordered_levels if lvl in severity_counts]
        # include any other unexpected levels at the end
        labels += [l for l in severity_counts.keys() if l not in labels]

        colors = [PALETTE['severity'].get(k, PALETTE['severity']['INFO']) for k in labels]

        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=[severity_counts[k] for k in labels],
                marker=dict(colors=colors),
                hovertemplate='<b>%{label}</b><br>Count: %{value} (%{percent})<extra></extra>',
                textinfo='label+percent',
                textfont=dict(size=14, color='#ffffff'),
                insidetextorientation='radial'
            )
        ])
        
        fig.update_layout(
            title='Alerts by Severity',
            template='plotly_dark',
            height=520,
            font=dict(family='Segoe UI, Arial, sans-serif', size=14, color='#ffffff'),
            legend=dict(font=dict(size=12)),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        logger.error(f"Error generating severity chart: {e}")
        return None


def generate_top_ips_chart():
    """Generate top attacking IPs chart"""
    try:
        alerts = db_manager.get_recent_alerts(limit=1000)
        
        if not alerts:
            return None
        
        ip_counts = Counter(a['src_ip'] for a in alerts)
        top_10 = dict(ip_counts.most_common(10))
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(top_10.values()),
                y=list(top_10.keys()),
                orientation='h',
                marker=dict(color=PALETTE['bars'][0]),
                hovertemplate='<b>%{y}</b><br>Alerts: %{x}<extra></extra>',
                text=list(top_10.values()),
                textposition='auto',
                textfont=dict(size=12, color='#ffffff')
            )
        ])

        fig.update_layout(
            title='Top 10 Attacking IPs',
            xaxis_title='Alert Count',
            yaxis_title='Source IP',
            template='plotly_dark',
            height=520,
            margin=dict(l=220, r=40, t=60, b=60),
            font=dict(family='Segoe UI, Arial, sans-serif', size=13, color='#ffffff'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        logger.error(f"Error generating top IPs chart: {e}")
        return None


def generate_top_signatures_chart():
    """Generate top attack signatures chart"""
    try:
        alerts = db_manager.get_recent_alerts(limit=1000)
        
        if not alerts:
            return None
        
        sig_counts = Counter(a['signature'] for a in alerts)
        top_10 = dict(sig_counts.most_common(10))
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(top_10.values()),
                y=list(top_10.keys()),
                orientation='h',
                marker=dict(color=PALETTE['bars'][2]),
                hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>',
                text=list(top_10.values()),
                textposition='auto',
                textfont=dict(size=12, color='#ffffff')
            )
        ])

        fig.update_layout(
            title='Top 10 Attack Signatures',
            xaxis_title='Count',
            yaxis_title='Signature',
            template='plotly_dark',
            height=520,
            margin=dict(l=320, r=40, t=60, b=60),
            font=dict(family='Segoe UI, Arial, sans-serif', size=13, color='#ffffff'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        logger.error(f"Error generating signatures chart: {e}")
        return None


# ==================== Routes ====================

@app.route('/')
def index():
    """Main dashboard page with real-time updates"""
    try:
        stats = db_manager.get_alert_stats()
        recent_alerts = db_manager.get_recent_alerts(limit=50)
        correlations = db_manager.get_correlations(limit=10)
        
        high_severity = sum(1 for a in recent_alerts if a['severity'] == 'HIGH')
        critical_severity = sum(1 for a in recent_alerts if a['severity'] == 'CRITICAL')
        
        # Generate charts
        timeline_chart = generate_alerts_timeline_chart()
        severity_chart = generate_severity_chart()
        top_ips_chart = generate_top_ips_chart()
        top_sigs_chart = generate_top_signatures_chart()
        
        return render_template('dashboard_enhanced.html',
                             stats=stats,
                             alerts=recent_alerts,
                             correlations=correlations,
                             high_count=high_severity,
                             critical_count=critical_severity,
                             timeline_chart=timeline_chart,
                             severity_chart=severity_chart,
                             top_ips_chart=top_ips_chart,
                             top_sigs_chart=top_sigs_chart,
                             last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/alerts')
def alerts():
    """All alerts page"""
    try:
        alerts = db_manager.get_recent_alerts(limit=100)
        return render_template('alerts.html', alerts=alerts)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/correlations')
def correlations():
    """Correlations page"""
    try:
        correlations = db_manager.get_correlations(limit=50)
        stats = db_manager.get_alert_stats()
        return render_template('correlations.html', correlations=correlations, stats=stats, last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/search', methods=['GET', 'POST'])
def search():
    """Advanced search with multiple filters"""
    try:
        query = request.args.get('query', '')
        query_type = request.args.get('query_type', 'ip')
        severity = request.args.get('severity', '')
        signature = request.args.get('signature', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        time_from = request.args.get('time_from', '')
        time_to = request.args.get('time_to', '')
        
        all_alerts = db_manager.get_recent_alerts(limit=1000)
        results = all_alerts
        
        # Filter by IP
        if query_type == 'ip' and query:
            results = [a for a in results if query.lower() in a['src_ip'].lower()]
        
        # Filter by signature
        if query_type == 'signature' and query:
            results = [a for a in results if query.lower() in a['signature'].lower()]
        
        # Filter by severity
        if severity:
            results = [a for a in results if a['severity'].upper() == severity.upper()]
        
        # Filter by signature name
        if signature:
            results = [a for a in results if signature.lower() in a['signature'].lower()]
        
        # Filter by date range with optional times
        if date_from:
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
            if time_from:
                time_from_obj = datetime.strptime(time_from, '%H:%M').time()
                date_from_dt = datetime.combine(date_from_dt.date(), time_from_obj)
            results = [a for a in results if datetime.fromisoformat(a['timestamp'].replace(' ', 'T')) >= date_from_dt]
        
        if date_to:
            date_to_dt = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            if time_to:
                time_to_obj = datetime.strptime(time_to, '%H:%M').time()
                date_to_dt = datetime.combine((datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)).date(), time_to_obj)
            results = [a for a in results if datetime.fromisoformat(a['timestamp'].replace(' ', 'T')) <= date_to_dt]
        
        return render_template('search_advanced.html',
                             results=results,
                             query=query,
                             query_type=query_type,
                             severity=severity,
                             signature=signature,
                             date_from=date_from,
                             date_to=date_to,
                             time_from=time_from,
                             time_to=time_to,
                             result_count=len(results))

    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/analytics')
def analytics():
    """Analytics dashboard with charts"""
    try:
        stats = db_manager.get_alert_stats()
        
        timeline_chart = generate_alerts_timeline_chart()
        severity_chart = generate_severity_chart()
        top_ips_chart = generate_top_ips_chart()
        top_sigs_chart = generate_top_signatures_chart()
        
        return render_template('analytics.html',
                             stats=stats,
                             timeline_chart=timeline_chart,
                             severity_chart=severity_chart,
                             top_ips_chart=top_ips_chart,
                             top_sigs_chart=top_sigs_chart)

    except Exception as e:
        return render_template('error.html', error=str(e)), 500


# ==================== API Endpoints ====================

@app.route('/api/alerts')
def api_alerts():
    """Get recent alerts as JSON"""
    try:
        limit = request.args.get('limit', 50, type=int)
        alerts = db_manager.get_recent_alerts(limit=limit)
        return jsonify({'success': True, 'alerts': alerts})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/alerts/ip/<ip>')
def api_alerts_by_ip(ip):
    """Get alerts from specific IP"""
    try:
        alerts = db_manager.get_alerts_by_ip(ip)
        return jsonify({'success': True, 'ip': ip, 'alerts': alerts, 'count': len(alerts)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/correlations')
def api_correlations():
    """Get correlations as JSON"""
    try:
        limit = request.args.get('limit', 10, type=int)
        correlations = db_manager.get_correlations(limit=limit)
        return jsonify({'success': True, 'correlations': correlations})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/stats')
def api_stats():
    """Get system statistics"""
    try:
        stats = db_manager.get_alert_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/enrich-ip/<ip>')
def api_enrich_ip(ip):
    """Enrich IP address with geolocation and organization data"""
    try:
        enrichment = ip_enricher.enrich_ip(ip)
        return jsonify({'success': True, 'ip': ip, 'enrichment': enrichment})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def api_search():
    """Advanced search API"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        query_type = data.get('query_type', 'ip')
        severity = data.get('severity', '')
        signature = data.get('signature', '')
        
        all_alerts = db_manager.get_recent_alerts(limit=1000)
        results = all_alerts
        
        if query_type == 'ip' and query:
            results = [a for a in results if query.lower() in a['src_ip'].lower()]
        
        if query_type == 'signature' and query:
            results = [a for a in results if query.lower() in a['signature'].lower()]
        
        if severity:
            results = [a for a in results if a['severity'].upper() == severity.upper()]
        
        if signature:
            results = [a for a in results if signature.lower() in a['signature'].lower()]
        
        return jsonify({'success': True, 'count': len(results), 'results': results})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


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


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', error='Page not found'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('error.html', error='Internal server error'), 500


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run Flask app with WebSocket support
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
