"""
Configuration file for Mini SIEM
"""

# Database settings
DATABASE_PATH = "data/siem.db"
DATABASE_BACKUP_PATH = "data/backups"

# Alert collection
SNORT_ALERT_FILE = "/var/log/snort/alert_fast.log"
COLLECTION_INTERVAL = 5  # seconds between checks
MOCK_ALERT_INTERVAL = 5  # seconds for mock generation

# Enrichment settings
IP_ENRICHMENT_ENABLED = True
IP_ENRICHMENT_CACHE_DURATION = 24  # hours
IP_ENRICHMENT_USE_FREE_API = True  # Use IP-API.com (free) vs MaxMind (paid)

# Correlation settings
CORRELATION_ANALYSIS_INTERVAL = 30  # seconds
CORRELATION_TIME_WINDOW = 10  # minutes
CORRELATION_ALERT_THRESHOLD = 5  # minimum alerts
CORRELATION_SIGNATURE_THRESHOLD = 3  # unique signatures

# Web interface settings
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
WEB_DEBUG = False
ALERTS_PER_PAGE = 50
CORRELATIONS_PER_PAGE = 20

# Data retention
ALERT_RETENTION_DAYS = 30  # Delete alerts older than this

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "mini_siem.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Severity levels
SEVERITY_LEVELS = {
    'CRITICAL': 1,
    'HIGH': 2,
    'MEDIUM': 3,
    'LOW': 4,
    'INFO': 5
}
