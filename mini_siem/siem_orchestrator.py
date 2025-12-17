"""
Main SIEM Orchestrator
Coordinates data collection, enrichment, storage, and correlation
"""

import logging
import time
import threading
from pathlib import Path
from datetime import datetime

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.database import DatabaseManager
from core.enricher import IPEnricher
from core.collector import AlertCollector, MockAlertGenerator
from core.correlator import CorrelationEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mini_siem.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class SIEMOrchestrator:
    """Main SIEM system orchestrator"""

    def __init__(self, use_mock_alerts: bool = False):
        """
        Initialize SIEM orchestrator
        
        Args:
            use_mock_alerts: Use mock alerts for testing (True) or real Snort alerts (False)
        """
        self.use_mock_alerts = use_mock_alerts
        self.db_manager = DatabaseManager()
        self.ip_enricher = IPEnricher(use_free_api=True)
        self.correlation_engine = CorrelationEngine(self.db_manager)
        self.alert_collector = AlertCollector()
        self.running = False
        self.thread = None

    def start(self):
        """Start the SIEM system"""
        logger.info("Starting Mini SIEM...")
        self.running = True

        # Start collection thread
        self.thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.thread.start()

        logger.info("Mini SIEM started successfully")

    def stop(self):
        """Stop the SIEM system"""
        logger.info("Stopping Mini SIEM...")
        self.running = False

        if self.thread:
            self.thread.join(timeout=5)

        if self.alert_collector:
            self.alert_collector.stop_collection()

        logger.info("Mini SIEM stopped")

    def _collection_loop(self):
        """Main collection and processing loop"""
        
        if not self.use_mock_alerts:
            # Try to start real alert collection
            if not self.alert_collector.start_collection():
                logger.warning("Could not start real alert collection, falling back to mock alerts")
                self.use_mock_alerts = True

        while self.running:
            try:
                # Collect new alerts
                if self.use_mock_alerts:
                    alerts = MockAlertGenerator.generate_batch(count=2)
                else:
                    alerts = self.alert_collector.read_new_alerts()

                if alerts:
                    self._process_alerts(alerts)

                # Run correlation analysis every 30 seconds
                if time.time() % 30 < 1:
                    self._analyze_correlations()

                # Sleep before next collection
                time.sleep(5)

            except Exception as e:
                logger.error(f"Error in collection loop: {str(e)}")
                time.sleep(10)

    def _process_alerts(self, alerts):
        """Process collected alerts"""
        for alert in alerts:
            try:
                # Enrich alert with IP information
                enriched_alert = self.ip_enricher.enrich_alert(alert)

                # Store in database
                alert_id = self.db_manager.insert_alert(enriched_alert)

                logger.info(f"Alert stored: {alert['signature']} from {alert['src_ip']} "
                           f"[ID: {alert_id}, Severity: {alert['severity']}]")

            except Exception as e:
                logger.error(f"Failed to process alert: {str(e)}")

    def _analyze_correlations(self):
        """Analyze alerts for suspicious patterns"""
        try:
            detections = self.correlation_engine.analyze_alerts()

            for detection in detections:
                try:
                    # Store correlation in database
                    corr_id = self.db_manager.insert_correlation(detection)

                    logger.warning(f"CORRELATION DETECTED: {detection['attack_type']} "
                                 f"from {detection['src_ip']} "
                                 f"[ID: {corr_id}, Severity: {detection.get('severity', 'HIGH')}]")

                except Exception as e:
                    logger.error(f"Failed to store correlation: {str(e)}")

        except Exception as e:
            logger.error(f"Error in correlation analysis: {str(e)}")

    def get_status(self):
        """Get system status"""
        stats = self.db_manager.get_alert_stats()
        return {
            'running': self.running,
            'use_mock_alerts': self.use_mock_alerts,
            'timestamp': datetime.now().isoformat(),
            'stats': stats
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Mini SIEM - Security Information and Event Management')
    parser.add_argument('--mock', action='store_true', help='Use mock alerts for testing')
    parser.add_argument('--web-only', action='store_true', help='Only run web interface (manual alert loading)')
    args = parser.parse_args()

    if args.web_only:
        # Just run the web interface
        from app.main import app
        logger.info("Starting Mini SIEM Web Interface only (no background collection)")
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        # Start full SIEM with background collection
        siem = SIEMOrchestrator(use_mock_alerts=args.mock)
        siem.start()

        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
            siem.stop()


if __name__ == '__main__':
    main()
