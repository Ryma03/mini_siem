"""
Correlation Engine for Mini SIEM
Detects suspicious patterns and correlates multiple alerts
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class CorrelationEngine:
    """Analyzes alerts to detect attack patterns"""

    def __init__(self, db_manager):
        """
        Initialize correlation engine
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
        self.time_window = 10  # minutes
        self.alert_threshold = 5  # alerts in time window
        self.signature_threshold = 3  # different signatures

    def analyze_alerts(self) -> List[Dict[str, Any]]:
        """
        Analyze recent alerts for suspicious patterns
        
        Returns:
            List of detected correlations
        """
        detections = []

        # Get all recent alerts
        recent_alerts = self.db.get_recent_alerts(limit=500)
        
        if not recent_alerts:
            return detections

        # Group by source IP
        ip_alerts = defaultdict(list)
        for alert in recent_alerts:
            ip_alerts[alert['src_ip']].append(alert)

        # Analyze each IP
        for src_ip, alerts in ip_alerts.items():
            # Pattern 1: High volume from single IP
            if len(alerts) >= self.alert_threshold:
                detection = self._detect_high_volume_attack(src_ip, alerts)
                if detection:
                    detections.append(detection)
                    self._log_detection(detection)

            # Pattern 2: Multiple different signatures from same IP
            unique_sigs = len(set(a['signature'] for a in alerts))
            if unique_sigs >= self.signature_threshold:
                detection = self._detect_multi_signature_attack(src_ip, alerts, unique_sigs)
                if detection:
                    detections.append(detection)
                    self._log_detection(detection)

            # Pattern 3: Rapid succession attacks
            if len(alerts) >= 2:
                detection = self._detect_rapid_attack(src_ip, alerts)
                if detection:
                    detections.append(detection)
                    self._log_detection(detection)

        return detections

    def _detect_high_volume_attack(self, src_ip: str, alerts: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        Detect high volume of alerts from same IP
        
        Args:
            src_ip: Source IP address
            alerts: List of alerts from that IP
            
        Returns:
            Detection dictionary or None
        """
        # Filter alerts by time window
        now = datetime.now()
        recent = [a for a in alerts if self._is_recent(a, self.time_window)]

        if len(recent) < self.alert_threshold:
            return None

        alert_times = sorted([a['timestamp'] for a in recent], reverse=True)
        first_alert = alert_times[-1]
        last_alert = alert_times[0]
        
        # Convert timestamps to datetime for time_span calculation
        first_alert_dt = self._parse_timestamp(first_alert)
        last_alert_dt = self._parse_timestamp(last_alert)
        time_span = (last_alert_dt - first_alert_dt).total_seconds()

        detection = {
            'attack_type': 'High Volume Attack (Possible DoS)',
            'src_ip': src_ip,
            'alert_count': len(recent),
            'unique_signatures': len(set(a['signature'] for a in recent)),
            'first_alert_time': first_alert,
            'last_alert_time': last_alert,
            'severity': 'HIGH',
            'details': {
                'reason': f"Detected {len(recent)} alerts in {self.time_window} minutes",
                'alert_signatures': list(set(a['signature'] for a in recent[:3])),
                'time_span_seconds': time_span
            }
        }

        return detection

    def _detect_multi_signature_attack(self, src_ip: str, alerts: List[Dict], 
                                       unique_sigs: int) -> Optional[Dict[str, Any]]:
        """
        Detect multiple different signatures from same IP
        
        Args:
            src_ip: Source IP address
            alerts: List of alerts from that IP
            unique_sigs: Number of unique signatures
            
        Returns:
            Detection dictionary or None
        """
        if unique_sigs < self.signature_threshold:
            return None

        recent = [a for a in alerts if self._is_recent(a, self.time_window)]
        
        if not recent:
            return None

        alert_times = sorted([a['timestamp'] for a in recent], reverse=True)
        
        signatures = [a['signature'] for a in recent]
        sig_counts = {}
        for sig in signatures:
            sig_counts[sig] = sig_counts.get(sig, 0) + 1

        detection = {
            'attack_type': 'Multi-Vector Attack (Probe/Reconnaissance)',
            'src_ip': src_ip,
            'alert_count': len(recent),
            'unique_signatures': len(set(signatures)),
            'first_alert_time': alert_times[-1] if alert_times else None,
            'last_alert_time': alert_times[0] if alert_times else None,
            'severity': 'HIGH',
            'details': {
                'reason': f"Detected {len(set(signatures))} different attack signatures",
                'signature_breakdown': sig_counts,
                'top_signatures': sorted(sig_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            }
        }

        return detection

    def _detect_rapid_attack(self, src_ip: str, alerts: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        Detect rapid succession of alerts (possible persistence attempt)
        
        Args:
            src_ip: Source IP address
            alerts: List of alerts from that IP
            
        Returns:
            Detection dictionary or None
        """
        if len(alerts) < 2:
            return None

        # Sort by timestamp
        sorted_alerts = sorted(alerts, key=lambda x: x['timestamp'])
        
        # Calculate time deltas between consecutive alerts
        rapid_attacks = []
        for i in range(1, len(sorted_alerts)):
            time_delta = (sorted_alerts[i]['timestamp'] - 
                         sorted_alerts[i-1]['timestamp']).total_seconds()
            
            # If alerts are within 30 seconds, it's rapid
            if 0 < time_delta < 30:
                rapid_attacks.append({
                    'alert1': sorted_alerts[i-1]['signature'],
                    'alert2': sorted_alerts[i]['signature'],
                    'time_delta': time_delta
                })

        if len(rapid_attacks) < 2:
            return None

        first_alert = sorted_alerts[0]['timestamp']
        last_alert = sorted_alerts[-1]['timestamp']

        detection = {
            'attack_type': 'Rapid Attack Sequence (Possible Exploitation)',
            'src_ip': src_ip,
            'alert_count': len(sorted_alerts),
            'unique_signatures': len(set(a['signature'] for a in sorted_alerts)),
            'first_alert_time': first_alert,
            'last_alert_time': last_alert,
            'severity': 'CRITICAL',
            'details': {
                'reason': f"Detected {len(rapid_attacks)} rapid attack sequences",
                'rapid_sequences': rapid_attacks[:5],
                'total_sequence_time': (last_alert - first_alert).total_seconds()
            }
        }

        return detection

    @staticmethod
    def _is_recent(alert: Dict, minutes: int) -> bool:
        """Check if alert is within time window"""
        if isinstance(alert['timestamp'], str):
            from datetime import datetime
            alert_time = datetime.fromisoformat(alert['timestamp'])
        else:
            alert_time = alert['timestamp']

        now = datetime.now()
        time_diff = (now - alert_time).total_seconds() / 60

        return time_diff < minutes

    @staticmethod
    def _log_detection(detection: Dict[str, Any]):
        """Log a detection event"""
        msg = (f"[{detection['severity']}] {detection['attack_type']} "
               f"from {detection['src_ip']} "
               f"({detection['alert_count']} alerts, "
               f"{detection['unique_signatures']} signatures)")
        
        if detection['severity'] == 'CRITICAL':
            logger.critical(msg)
        elif detection['severity'] == 'HIGH':
            logger.warning(msg)
        else:
            logger.info(msg)

    def set_time_window(self, minutes: int):
        """Set correlation time window"""
        self.time_window = minutes

    def set_alert_threshold(self, count: int):
        """Set minimum alert count for detection"""
        self.alert_threshold = count

    def set_signature_threshold(self, count: int):
        """Set minimum signature count for detection"""
        self.signature_threshold = count

    @staticmethod
    def _parse_timestamp(ts) -> datetime:
        """Convert timestamp string or datetime to datetime object"""
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts)
            except:
                # Try parsing with space separator
                return datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
        return ts

