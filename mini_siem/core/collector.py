"""
Alert Collector module for Mini SIEM
Reads and parses Snort alerts from log files in real-time
"""

import re
import logging
import time
import random
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SnortAlertParser:
    """Parses Snort alerts from the alert_fast.log file"""

    # Snort alert format regex for full alert format
    # Example: 12/17-18:21:52.730564  [**] [1:1917:6] SCAN UPnP service discover attempt [**] [Classification: Detection of a Network Scan] [Priority: 3] {UDP} 192.168.1.62:54670 -> 239.255.255.250:1900
    SNORT_ALERT_REGEX = re.compile(
        r"(\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)\s+"
        r"\[\*\*\]\s+\[[\d:]+\]\s+([^\[]+?)\s+\[\*\*\]\s+"
        r"\[Classification:\s*([^\]]+)\]\s+\[Priority:\s*(\d+)\]\s+"
        r"\{([A-Z]+)\}\s+"
        r"([0-9.]+):(\d+)\s+->\s+([0-9.]+):(\d+)"
    )

    # Priority levels mapping to severity
    SEVERITY_MAP = {
        '1': 'HIGH',
        '2': 'MEDIUM',
        '3': 'LOW',
        '4': 'INFO'
    }

    def __init__(self):
        """Initialize the parser"""
        self.last_position = 0

    def parse_snort_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single Snort alert line
        
        Args:
            line: Raw alert line from Snort log
            
        Returns:
            Dictionary with parsed alert data or None
        """
        match = self.SNORT_ALERT_REGEX.search(line)
        if not match:
            return None

        try:
            timestamp_str, signature, classification, priority, protocol, src_ip, src_port, dst_ip, dst_port = match.groups()

            # Parse timestamp
            timestamp = datetime.strptime(timestamp_str, "%m/%d-%H:%M:%S.%f")
            
            # Clean up signature
            signature = signature.strip()

            alert = {
                'timestamp': timestamp,
                'signature': signature,
                'classification': classification.strip(),
                'priority': priority,
                'severity': self.SEVERITY_MAP.get(priority, 'INFO'),
                'protocol': protocol,
                'src_ip': src_ip,
                'src_port': int(src_port),
                'dst_ip': dst_ip,
                'dst_port': int(dst_port),
                'message': line.strip()
            }

            return alert

        except Exception as e:
            logger.warning(f"Failed to parse alert line: {str(e)}")
            return None

    def parse_csv_format(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse Snort CSV format alert
        Format: timestamp,sig_generator,sig_id,sig_rev,msg,proto,src,srcport,dst,dstport,id,classification,priority
        
        Args:
            line: CSV formatted alert line
            
        Returns:
            Parsed alert dictionary
        """
        try:
            parts = [p.strip('"') for p in line.split(',')]
            
            if len(parts) < 13:
                return None

            timestamp = datetime.fromisoformat(parts[0])
            
            alert = {
                'timestamp': timestamp,
                'signature': parts[4],  # msg
                'classification': parts[11],
                'priority': parts[12],
                'severity': self.SEVERITY_MAP.get(parts[12], 'INFO'),
                'protocol': parts[5],
                'src_ip': parts[6],
                'src_port': int(parts[7]) if parts[7] else 0,
                'dst_ip': parts[8],
                'dst_port': int(parts[9]) if parts[9] else 0,
                'message': f"{parts[4]} - {parts[6]}:{parts[7]} -> {parts[8]}:{parts[9]}"
            }

            return alert

        except Exception as e:
            logger.warning(f"Failed to parse CSV alert line: {str(e)}")
            return None


class AlertCollector:
    """Collects alerts from Snort log file in real-time"""

    def __init__(self, alert_file: str = "/var/log/snort/alert_fast.log"):
        """
        Initialize alert collector
        
        Args:
            alert_file: Path to Snort alert log file
        """
        self.alert_file = alert_file
        self.parser = SnortAlertParser()
        self.last_position = 0
        self.file_handle = None

    def start_collection(self) -> bool:
        """
        Open and prepare alert file for collection
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not Path(self.alert_file).exists():
                logger.error(f"Alert file not found: {self.alert_file}")
                return False

            self.file_handle = open(self.alert_file, 'r', encoding='utf-8', errors='ignore')
            # Move to end of file
            self.file_handle.seek(0, 2)
            self.last_position = self.file_handle.tell()
            logger.info(f"Alert collection started on {self.alert_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to start collection: {str(e)}")
            return False

    def read_new_alerts(self) -> List[Dict[str, Any]]:
        """
        Read new alerts from the log file
        
        Returns:
            List of new alert dictionaries
        """
        alerts = []

        try:
            if not self.file_handle:
                self.start_collection()

            self.file_handle.seek(self.last_position)
            new_lines = self.file_handle.readlines()
            self.last_position = self.file_handle.tell()

            for line in new_lines:
                if not line.strip():
                    continue

                # Try parsing as fast format first
                alert = self.parser.parse_snort_line(line)
                
                # If that fails, try CSV format
                if not alert:
                    alert = self.parser.parse_csv_format(line)

                if alert:
                    alerts.append(alert)

            return alerts

        except Exception as e:
            logger.error(f"Error reading alerts: {str(e)}")
            return []

    def stop_collection(self):
        """Stop collection and close file"""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
            logger.info("Alert collection stopped")

    def __enter__(self):
        """Context manager entry"""
        self.start_collection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_collection()


class MockAlertGenerator:
    """Generates mock Snort alerts for testing without actual IDS"""

    SIGNATURES = [
        "Potential SSH Brute Force",
        "Web Application SQL Injection Attempt",
        "Port Scanning Detected",
        "Unauthorized Data Transfer",
        "Suspicious DNS Query",
        "Malware Command and Control Traffic",
        "Directory Traversal Attempt",
        "Buffer Overflow Attempt",
        "Denial of Service Attack",
        "Suspicious Network Activity"
    ]

    PROTOCOLS = ["TCP", "UDP", "ICMP", "HTTP", "HTTPS"]

    @classmethod
    def generate_alert(cls) -> Dict[str, Any]:
        """Generate a random mock alert"""
        import random
        
        base_ip = f"192.168.{random.randint(0, 255)}"
        
        alert = {
            'timestamp': datetime.now() - timedelta(seconds=random.randint(0, 3600)),
            'signature': random.choice(cls.SIGNATURES),
            'classification': 'Suspicious Activity',
            'priority': str(random.randint(1, 3)),
            'severity': random.choice(['HIGH', 'MEDIUM', 'LOW']),
            'protocol': random.choice(cls.PROTOCOLS),
            'src_ip': f"{base_ip}.{random.randint(1, 254)}",
            'src_port': random.randint(1024, 65535),
            'dst_ip': "10.0.0.1",
            'dst_port': random.choice([22, 80, 443, 3306, 5432]),
            'message': f"Mock alert for testing"
        }

        return alert

    @classmethod
    def generate_batch(cls, count: int = 10) -> List[Dict[str, Any]]:
        """Generate multiple mock alerts"""
        return [cls.generate_alert() for _ in range(count)]
