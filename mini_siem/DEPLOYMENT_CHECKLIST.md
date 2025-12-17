# Mini SIEM Deployment Checklist

## Pre-Deployment Phase

### Environment Validation
- [ ] Python 3.10+ installed
  ```bash
  python --version  # Should be 3.10 or higher
  ```
- [ ] Git installed (optional but recommended)
- [ ] pip package manager available
- [ ] Virtual environment tool available (`python -m venv`)

### System Preparation

#### Windows (Development/Testing)
- [ ] Administrator access for pip installation
- [ ] PowerShell or CMD terminal available
- [ ] 500MB free disk space
- [ ] No antivirus blocking Python/pip

#### Linux/Ubuntu (Production)
- [ ] Ubuntu 18.04 LTS or newer
- [ ] `sudo` access for package installation
- [ ] 1GB free disk space
- [ ] Network connectivity
- [ ] Snort dependencies available: `libpcap-dev`, `libnet1-dev`, `libnetfilter-queue-dev`

### Repository Setup
- [ ] Clone or download project to target directory
- [ ] Verify directory structure exists:
  ```
  mini_siem/
  ├── app/
  │   ├── main.py
  │   └── templates/
  ├── core/
  │   ├── database.py
  │   ├── enricher.py
  │   ├── collector.py
  │   └── correlator.py
  ├── static/
  │   └── style.css
  ├── data/
  ├── requirements.txt
  ├── config.py
  ├── siem_orchestrator.py
  ├── test_suite.py
  └── README.md
  ```

---

## Installation Phase

### Step 1: Install Python Dependencies
```bash
# Windows or Linux
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Expected Duration:** 2-3 minutes
**Success Indicator:** No error messages, all packages listed in `pip list`

Required packages:
- [ ] Flask==2.3.3
- [ ] requests==2.31.0
- [ ] ipwhois==1.2.0
- [ ] Werkzeug==2.3.7

### Step 2: Verify Installation
```bash
python -c "import flask, requests, ipwhois; print('✓ All dependencies loaded')"
```

**Expected Output:** `✓ All dependencies loaded`

### Step 3: Create Data Directory
```bash
# Windows
mkdir data
# or Linux
mkdir -p data
```

- [ ] `data/` directory created
- [ ] Directory is writable (test by creating temp file)

### Step 4: Run Test Suite
```bash
python test_suite.py
```

**Expected Output:**
```
test_database ... ok
test_enricher ... ok
test_collector ... ok
test_correlator ... ok
test_end_to_end ... ok

Ran 5 tests in X.XXXs
OK
```

**Success Indicators:**
- [ ] All 5 tests pass
- [ ] No import errors
- [ ] Database created in `data/alerts.db`

---

## Snort Setup (Linux Only)

### Step 1: Install Snort
```bash
sudo apt-get update
sudo apt-get install -y snort
```

**Duration:** 3-5 minutes

- [ ] Snort installed successfully
- [ ] Version check: `snort --version`

### Step 2: Create Snort Directories
```bash
sudo mkdir -p /var/log/snort
sudo mkdir -p /etc/snort/rules
sudo chmod 755 /var/log/snort
sudo touch /var/log/snort/alert_fast.log
sudo chmod 666 /var/log/snort/alert_fast.log
```

- [ ] `/var/log/snort/` directory created
- [ ] `alert_fast.log` file created and writable
- [ ] Permissions set correctly

### Step 3: Configure Snort (Basic)
```bash
sudo nano /etc/snort/snort.conf
```

**Add to snort.conf:**
```
output fast: /var/log/snort/alert_fast.log
```

- [ ] Output rule added to snort.conf
- [ ] File saved

### Step 4: Start Snort
```bash
# Test mode (don't actually run)
sudo snort -c /etc/snort/snort.conf -T

# Run in background
sudo snort -c /etc/snort/snort.conf -l /var/log/snort -A fast -D

# Or run in foreground (for testing)
sudo snort -c /etc/snort/snort.conf -l /var/log/snort -A fast
```

- [ ] Snort started without errors
- [ ] Log file being written: `tail -f /var/log/snort/alert_fast.log`

---

## Application Setup

### Step 1: Start Background Collector

**Option A: With Mock Data (Testing)**
```bash
python siem_orchestrator.py --mock
```

Expected output:
```
[INFO] Starting Mini SIEM Orchestrator...
[INFO] Using MOCK alert generation
[INFO] Collection loop started
[INFO] Correlation loop started
```

- [ ] Process running without errors
- [ ] Logs visible in console
- [ ] Database receiving mock alerts

**Option B: With Real Snort (Production)**
```bash
python siem_orchestrator.py
```

Expected output:
```
[INFO] Starting Mini SIEM Orchestrator...
[INFO] Reading from /var/log/snort/alert_fast.log
[INFO] Collection loop started
[INFO] Correlation loop started
```

- [ ] Process running without errors
- [ ] Waiting for alerts from Snort

### Step 2: Start Web Server (New Terminal)
```bash
python app/main.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: off
 * Press CTRL+C to quit
```

- [ ] Flask server started
- [ ] Listening on port 5000
- [ ] No errors in startup

### Step 3: Verify Web Interface
```bash
# Test in another terminal
curl http://localhost:5000/
```

- [ ] HTTP 200 response
- [ ] HTML dashboard returned
- [ ] No connection errors

### Step 4: Access Dashboard
Open browser to: `http://localhost:5000`

- [ ] Dashboard loads without errors
- [ ] Stats cards visible
- [ ] Alert table visible (may be empty if no alerts yet)

---

## Testing & Validation

### Unit Tests
```bash
python test_suite.py
```

- [ ] All 5 tests pass
- [ ] No failures reported
- [ ] Execution time < 10 seconds

### Database Validation
```bash
python -c "from core.database import DatabaseManager; db = DatabaseManager(); print('✓ Database OK'); print(f'Alert count: {db.get_alert_count()}')"
```

- [ ] Database connects successfully
- [ ] Can query alert count
- [ ] No corruption errors

### API Testing
```bash
# Get recent alerts
curl http://localhost:5000/api/alerts

# Get stats
curl http://localhost:5000/api/stats

# Search by IP (if alerts exist)
curl "http://localhost:5000/api/search?query=192.168"
```

- [ ] All API endpoints respond with JSON
- [ ] Status codes are 200 OK
- [ ] Response format is valid

### Alert Generation (Linux with Snort)
```bash
# Terminal 1: Monitor alerts
tail -f /var/log/snort/alert_fast.log

# Terminal 2: Generate network traffic
nmap -sV localhost
ping -c 10 localhost
nmap -p22 localhost
```

- [ ] Snort generates alerts in log file
- [ ] SIEM collector picks up alerts
- [ ] Alerts appear in web dashboard within 10 seconds

### Correlation Testing (with 30+ alerts)
```bash
# Run with mock to generate multiple alerts quickly
python siem_orchestrator.py --mock

# Wait 2-3 minutes for correlation engine to analyze
# Check /api/correlations endpoint for detected patterns
curl http://localhost:5000/api/correlations
```

- [ ] Correlations detected (should see attack patterns)
- [ ] Correlation dashboard shows detected patterns
- [ ] Event counts and timelines displayed

---

## Configuration Review

### Before Production Deployment

**Review config.py:**
```python
# Database settings
DB_PATH = 'data/alerts.db'
RETENTION_DAYS = 30  # Adjust if needed

# Collection settings
COLLECTION_INTERVAL = 5  # seconds
CORRELATION_WINDOW = 600  # 10 minutes
CORRELATION_INTERVAL = 30  # seconds

# Correlation thresholds
HIGH_VOLUME_THRESHOLD = 5  # alerts in time window
MULTI_SIGNATURE_THRESHOLD = 3  # unique signatures
RAPID_SEQUENCE_THRESHOLD = 30  # seconds
```

- [ ] Database retention acceptable
- [ ] Collection interval appropriate for your environment
- [ ] Correlation thresholds match your network baseline
- [ ] Web port not in use (check: `netstat -an | grep 5000`)

**Optional Adjustments:**
- [ ] Switch enrichment to paid API (MaxMind) if desired
- [ ] Configure Snort for your network rules
- [ ] Set up log rotation for alert logs
- [ ] Configure backup storage for database

---

## Production Considerations

### Linux Deployment
```bash
# Create systemd service
sudo nano /etc/systemd/system/mini-siem-collector.service

[Unit]
Description=Mini SIEM Collector
After=network.target snort.service

[Service]
Type=simple
User=siem
ExecStart=/usr/bin/python3 /opt/mini_siem/siem_orchestrator.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

- [ ] Service file created (optional but recommended)
- [ ] Service can be started: `sudo systemctl start mini-siem-collector`
- [ ] Service auto-starts on boot: `sudo systemctl enable mini-siem-collector`

### Performance Optimization
- [ ] Monitor CPU usage: `top -p $(pgrep -f siem_orchestrator)`
- [ ] Monitor memory: `ps aux | grep siem_orchestrator`
- [ ] Check disk space: `df -h data/`
- [ ] Review logs: `tail -f mini_siem.log`

### Backup Strategy
- [ ] Backup database regularly: `cp data/alerts.db data/alerts.db.backup`
- [ ] Rotate old databases: `find data/ -name "*.db.backup*" -mtime +30 -delete`
- [ ] Archive logs: `gzip mini_siem.log`

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask'"
**Solution:**
```bash
pip install -r requirements.txt
python -c "import flask; print(flask.__version__)"
```

### Issue: Port 5000 already in use
**Solution:**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux
lsof -i :5000
kill -9 <PID>

# Or change port in app/main.py: app.run(port=8080)
```

### Issue: Snort not generating alerts
**Solution:**
1. Check Snort is running: `ps aux | grep snort`
2. Check log file exists: `ls -la /var/log/snort/`
3. Check log file permissions: `sudo chmod 666 /var/log/snort/alert_fast.log`
4. Generate network traffic: `nmap localhost`
5. Monitor log: `tail -f /var/log/snort/alert_fast.log`

### Issue: Database locked error
**Solution:**
1. Check if multiple instances running: `ps aux | grep siem_orchestrator`
2. Kill duplicate process: `pkill -f siem_orchestrator`
3. Delete lock file: `rm data/alerts.db-wal data/alerts.db-shm`
4. Restart: `python siem_orchestrator.py`

### Issue: Web dashboard shows "No data"
**Solution:**
- Check collector is running: `ps aux | grep siem_orchestrator`
- Check database: `python -c "from core.database import DatabaseManager; print(DatabaseManager().get_alert_count())"`
- Check logs: `tail -f mini_siem.log`
- For testing: `python siem_orchestrator.py --mock` generates test alerts

---

## Completion Checklist

### System Ready for Testing
- [ ] All unit tests pass
- [ ] Database created and accessible
- [ ] Collector running without errors
- [ ] Web server running without errors
- [ ] Dashboard accessible via browser

### System Ready for Production
- [ ] Snort installed and running (Linux)
- [ ] Snort generating alerts to log file
- [ ] Alerts appearing in dashboard within 10 seconds
- [ ] Correlations detected for pattern analysis
- [ ] All API endpoints responding with valid JSON
- [ ] No Python errors in logs
- [ ] Database backup strategy in place
- [ ] Performance metrics established
- [ ] Documentation reviewed

### Deployment Complete
- [ ] System is stable under normal load
- [ ] Alert collection working reliably
- [ ] Enrichment data accurate
- [ ] Correlations meaningful
- [ ] Web interface responsive
- [ ] Regular backups running
- [ ] Monitoring in place

---

## Support & Next Steps

### Documentation
- See `README.md` for detailed feature documentation
- See `config.py` for all configuration options
- Check `core/` modules for implementation details

### Log Files
- Application logs: `mini_siem.log`
- Snort logs: `/var/log/snort/alert_fast.log`
- Flask debug: Console output when `app/main.py` runs

### Common Tasks
- **View recent alerts:** `http://localhost:5000/alerts`
- **Search alerts:** `http://localhost:5000/search`
- **Check stats:** `http://localhost:5000/api/stats`
- **Clear old alerts:** `python -c "from core.database import DatabaseManager; DatabaseManager().clear_old_alerts(7)"`

### Performance Tuning
If you experience high CPU/memory usage:
1. Increase `COLLECTION_INTERVAL` in config.py (5 → 10 seconds)
2. Increase `CORRELATION_INTERVAL` in config.py (30 → 60 seconds)
3. Reduce `HIGH_VOLUME_THRESHOLD` correlation threshold
4. Check disk space: `df -h`
5. Archive old databases

---

**Estimated Total Setup Time:**
- Windows (with mock alerts): 10-15 minutes
- Linux (with Snort): 30-45 minutes
- Both systems: First run to see alerts: 5 minutes
- Full validation: 15-20 minutes

**Questions or Issues?** Check README.md troubleshooting section or review logs.
