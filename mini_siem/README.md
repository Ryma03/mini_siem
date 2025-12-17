# Mini SIEM - Security Information and Event Management System

A lightweight prototype SIEM system built with Python, Flask, and SQLite for detecting and analyzing network security threats using Snort IDS.

## 🎯 Features

- **Real-time Alert Collection**: Reads Snort alerts from log files
- **IP Enrichment**: Adds geolocation, ASN, and organization data to alerts
- **Alert Normalization**: Standardizes alerts into consistent format
- **Correlation Detection**: Identifies attack patterns and suspicious behavior clusters
- **SQLite Database**: Persistent storage of all alerts and correlations
- **Flask Web Dashboard**: Beautiful, responsive web interface for visualization
- **Mock Alert Generator**: Test system without running actual Snort

## 📋 Requirements

### Python
- Python 3.10+
- pip3 (Python package manager)

### Python Dependencies
- Flask 2.3.3
- Requests 2.31.0
- ipwhois 1.2.0
- Werkzeug 2.3.7

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Windows
pip install -r requirements.txt

# macOS/Linux
pip3 install -r requirements.txt
```

### 2. Run with Mock Alerts (Testing)

```bash
# Terminal 1 - Start collector with mock data
python siem_orchestrator.py --mock

# Terminal 2 - Start web dashboard
python app/main.py

# Open browser to: http://localhost:5000
```

### 3. Verify Installation

```bash
# Run test suite
python test_suite.py

# Expected output: All 5 tests should pass
```

## 📁 Project Structure

```
mini_siem/
├── app/
│   ├── main.py                 # Flask web application
│   ├── templates/              # HTML templates
│   │   ├── dashboard.html      # Main dashboard
│   │   ├── alerts.html         # All alerts view
│   │   ├── correlations.html   # Detected correlations
│   │   ├── search.html         # Search interface
│   │   └── error.html          # Error page
│   └── static/                 # Static files (CSS, JS)
│
├── core/
│   ├── database.py             # SQLite database management
│   ├── collector.py            # Snort alert collection & parsing
│   ├── enricher.py             # IP enrichment (geolocation, ASN)
│   └── correlator.py           # Correlation detection engine
│
├── data/
│   └── siem.db                 # SQLite database (auto-created)
│
├── siem_orchestrator.py        # Main system orchestrator
├── requirements.txt            # Python dependencies
├── install.sh                  # Installation script
├── install.bat                 # Windows installation helper
└── README.md                   # This file
```

## 🔧 Configuration

### Application Configuration
Edit `config.py` to customize:

```python
# Database settings
DB_PATH = 'data/alerts.db'
RETENTION_DAYS = 30  # Keep alerts for 30 days

# Collection intervals (in seconds)
COLLECTION_INTERVAL = 5  # Check for new alerts every 5 seconds
CORRELATION_INTERVAL = 30  # Run correlation analysis every 30 seconds
CORRELATION_WINDOW = 600  # 10-minute window for grouping alerts

# Correlation thresholds
HIGH_VOLUME_THRESHOLD = 5  # 5+ alerts = potential DoS
MULTI_SIGNATURE_THRESHOLD = 3  # 3+ signatures = reconnaissance
RAPID_SEQUENCE_THRESHOLD = 30  # <30 seconds between alerts = exploitation

# Web interface
WEB_HOST = '127.0.0.1'
WEB_PORT = 5000
```

### IP Enrichment Configuration
Edit `core/enricher.py` to choose enrichment provider:

```python
# Option 1: Free IP-API.com (default, no API key needed)
USE_PAID_API = False

# Option 2: MaxMind GeoIP2 (requires API key)
USE_PAID_API = True
MAXMIND_LICENSE_KEY = 'your_license_key'
```

### Alert Log Path (for Ubuntu Snort deployment)
The collector reads from: `/var/log/snort/alert_fast.log`

When you deploy to Ubuntu with Snort, ensure:
1. Snort writes alerts to `/var/log/snort/alert_fast.log`
2. Log file is readable by your user
3. Update `config.py` if path is different on your system

## 📋 Implementation Code Overview

The system consists of 4 core modules:

### 1. **database.py** - Alert Storage
```python
DatabaseManager()
  ├─ insert_alert(alert_dict)
  ├─ get_recent_alerts(limit=50)
  ├─ get_alerts_by_ip(ip_address)
  ├─ insert_correlation(pattern)
  ├─ get_correlations(limit=10)
  └─ get_alert_stats()
```

### 2. **collector.py** - Alert Collection
```python
AlertCollector()          # Real-time Snort log reading
  ├─ read_new_alerts()   # Tail log file for new alerts
  └─ parse_snort_line()  # Parse Snort fast format

MockAlertGenerator()       # For testing without Snort
  └─ generate_batch()    # Create realistic test alerts
```

### 3. **enricher.py** - IP Information
```python
IPEnricher()
  ├─ enrich_ip(ip)       # Get geolocation, ASN, org
  ├─ enrich_alert()      # Add enrichment to alert dict
  └─ cache mechanism     # 24-hour cache to reduce API calls
```

### 4. **correlator.py** - Attack Detection
```python
CorrelationEngine()
  ├─ analyze_alerts()                      # Main analysis method
  ├─ _detect_high_volume_attack()          # DoS detection
  ├─ _detect_multi_signature_attack()      # Reconnaissance
  └─ _detect_rapid_attack()                # Exploitation patterns
```

## 📊 Dashboard Features

### Main Dashboard
- **Statistics**: Total alerts, critical alerts, unique IPs, correlations
- **Recent Alerts**: Last 50 alerts with color-coded severity
- **Real-time Updates**: Auto-refresh capability

### All Alerts View
- Complete alert history (last 100)
- Searchable and sortable
- Full enrichment data visible

### Correlations View
- Detected attack patterns
- Pattern details and timeline
- Severity classification

### Search
- Search by IP address
- Search by signature
- Filter by severity

## 🎯 Alert Types & Severity Levels

### Severity Levels
- **CRITICAL** (Red): Immediate attention required
- **HIGH** (Orange): Significant security threat
- **MEDIUM** (Blue): Noteworthy activity
- **LOW** (Green): Informational

### Correlation Detection Patterns

1. **High Volume Attack (DoS)**
   - Multiple alerts from same IP in time window
   - Indicates possible denial of service attempt

2. **Multi-Vector Attack (Reconnaissance)**
   - Multiple different signatures from same IP
   - Indicates possible probe/reconnaissance activity

3. **Rapid Attack Sequence**
   - Rapid succession of alerts (< 30 seconds apart)
   - Indicates possible exploitation attempt

## 🧪 Testing

### Quick Test with Mock Alerts
```bash
# No real network traffic needed - uses simulated data
python siem_orchestrator.py --mock

# Open browser: http://localhost:5000
# You'll see generated test alerts
```

### Verify All Components Work
```bash
# Run the test suite
python test_suite.py

# Expected output: All 5 tests pass ✓
```

## 📝 Database Schema

### Alerts Table
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    signature TEXT,
    src_ip TEXT,
    dst_ip TEXT,
    src_port INTEGER,
    dst_port INTEGER,
    protocol TEXT,
    severity TEXT,
    message TEXT,
    timestamp DATETIME,
    enrichment_data TEXT,
    created_at DATETIME
);
```

### Correlations Table
```sql
CREATE TABLE correlations (
    id INTEGER PRIMARY KEY,
    attack_type TEXT,
    src_ip TEXT,
    alert_count INTEGER,
    unique_signatures INTEGER,
    first_alert_time DATETIME,
    last_alert_time DATETIME,
    details TEXT,
    created_at DATETIME
);
```

## 🔒 Security Considerations

⚠️ **Important**: This is a prototype/educational system. When deploying to production:
- Add HTTPS/TLS encryption for web interface
- Implement authentication and authorization
- Run on isolated network segment
- Establish log retention policies
- Set up regular backups
- Monitor system performance and resource usage

## 🐛 Troubleshooting

### Dependencies not installing
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Then install requirements
pip install -r requirements.txt

# Verify installation
python -c "import flask, requests, ipwhois; print('✓ OK')"
```

### Web interface not accessible
1. Check Flask is running: See console output
2. Verify port 5000 is available: `netstat -an | findstr 5000`
3. Use different port in `app/main.py`: `app.run(port=8080)`

### Database errors
1. Delete old database: `rm data/alerts.db`
2. Restart the system - database recreates automatically
3. Check disk space: `df -h` (Linux) or `dir` (Windows)

### Collector not finding alerts
When you deploy to Ubuntu with Snort:
1. Ensure Snort writes to `/var/log/snort/alert_fast.log`
2. Make log file readable: `chmod 644 /var/log/snort/alert_fast.log`
3. Update alert file path in `config.py` if different

## 📚 API Endpoints

```
GET  /                      - Main dashboard
GET  /alerts                - All alerts page
GET  /correlations          - Correlations page
GET  /search                - Search interface

GET  /api/alerts            - Get recent alerts (JSON)
GET  /api/alerts/ip/<ip>    - Alerts from IP (JSON)
GET  /api/correlations      - Get correlations (JSON)
GET  /api/enrich-ip/<ip>    - Enrich IP address (JSON)
GET  /api/stats             - System statistics (JSON)
GET  /api/alerts/severity/<sev> - Alerts by severity (JSON)
```

## 🚀 Ubuntu Deployment

When ready to deploy to Ubuntu with Snort:

1. **Install Python 3.10+** on Ubuntu machine
2. **Copy all code files** to Ubuntu system
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Install Snort**: `sudo apt-get install snort`
5. **Configure Snort** to write alerts to `/var/log/snort/alert_fast.log`
6. **Run collector**: `python siem_orchestrator.py`
7. **Run web server**: `python app/main.py`
8. **Access dashboard**: `http://your_ubuntu_ip:5000`

The code is production-ready - just set up Snort on Ubuntu when you're ready!

## 🤝 Contributing

Improvements welcome! Areas for enhancement:
- Additional correlation patterns
- Real-time WebSocket updates
- Machine learning anomaly detection
- Advanced filtering and visualization
- Performance optimization

## 📄 License

Educational/Prototype project. Use for learning purposes.

## 👨‍💼 Implementation Overview

This Mini SIEM project includes:
- **Complete Python codebase** - 4 core modules + Flask web app (1000+ lines)
- **SQLite database** - Alerts + correlations tables with indexing
- **Real-time alert processing** - Snort log parsing with regex extraction
- **IP enrichment** - Geolocation and organization data with caching
- **Attack detection** - 3 correlation patterns (DoS, reconnaissance, exploitation)
- **Web dashboard** - 5 responsive pages + 6 JSON APIs
- **Test suite** - Comprehensive validation of all components
- **Mock alerts** - Generate realistic test data without Snort

All code is documented with docstrings and ready to deploy!

---

**Version**: 1.0 (Production-ready implementation)
**Status**: Ready for deployment to Ubuntu + Snort
**Last Updated**: December 2025
