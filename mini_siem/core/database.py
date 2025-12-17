"""
Database module for Mini SIEM
Handles SQLite database operations for alert storage and retrieval
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "siem.db"


class DatabaseManager:
    """Manages SQLite database operations"""

    def __init__(self, db_path: str = str(DB_PATH)):
        """Initialize database connection"""
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Create database and tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signature TEXT NOT NULL,
                    src_ip TEXT NOT NULL,
                    dst_ip TEXT NOT NULL,
                    src_port INTEGER,
                    dst_port INTEGER,
                    protocol TEXT,
                    severity TEXT,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    enrichment_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create correlations table for detected attacks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS correlations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attack_type TEXT NOT NULL,
                    src_ip TEXT NOT NULL,
                    alert_count INTEGER,
                    unique_signatures INTEGER,
                    first_alert_time DATETIME,
                    last_alert_time DATETIME,
                    details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create blocked IPs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_ips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT UNIQUE NOT NULL,
                    reason TEXT,
                    blocked_by TEXT DEFAULT 'admin',
                    blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indices for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_src_ip ON alerts(src_ip)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON alerts(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_severity ON alerts(severity)
            """)
            
            conn.commit()

    def insert_alert(self, alert: Dict[str, Any]) -> int:
        """
        Insert a single alert into the database
        
        Args:
            alert: Dictionary containing alert data
            
        Returns:
            Alert ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            enrichment_data = json.dumps(alert.get('enrichment', {}))
            
            cursor.execute("""
                INSERT INTO alerts 
                (signature, src_ip, dst_ip, src_port, dst_port, protocol, 
                 severity, message, timestamp, enrichment_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.get('signature', ''),
                alert.get('src_ip', ''),
                alert.get('dst_ip', ''),
                alert.get('src_port', None),
                alert.get('dst_port', None),
                alert.get('protocol', ''),
                alert.get('severity', 'INFO'),
                alert.get('message', ''),
                alert.get('timestamp', datetime.now()),
                enrichment_data
            ))
            
            conn.commit()
            return cursor.lastrowid

    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get the most recent alerts
        
        Args:
            limit: Number of alerts to retrieve
            
        Returns:
            List of alert dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM alerts 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            alerts = []
            
            for row in rows:
                alert_dict = dict(row)
                # Parse enrichment data
                if alert_dict['enrichment_data']:
                    alert_dict['enrichment'] = json.loads(alert_dict['enrichment_data'])
                else:
                    alert_dict['enrichment'] = {}
                
                alerts.append(alert_dict)
            
            return alerts

    def get_alerts_by_ip(self, src_ip: str, minutes: int = 10) -> List[Dict[str, Any]]:
        """
        Get alerts from a specific IP within the last X minutes
        
        Args:
            src_ip: Source IP address
            minutes: Time window in minutes
            
        Returns:
            List of alert dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM alerts 
                WHERE src_ip = ? 
                AND datetime(timestamp) > datetime('now', '-' || ? || ' minutes')
                ORDER BY timestamp DESC
            """, (src_ip, minutes))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_alert_count_by_ip(self, src_ip: str, minutes: int = 10) -> int:
        """Count alerts from an IP in the last X minutes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM alerts 
                WHERE src_ip = ? 
                AND datetime(timestamp) > datetime('now', '-' || ? || ' minutes')
            """, (src_ip, minutes))
            
            return cursor.fetchone()[0]

    def get_unique_signatures_by_ip(self, src_ip: str, minutes: int = 10) -> int:
        """Count unique signatures from an IP in the last X minutes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(DISTINCT signature) FROM alerts 
                WHERE src_ip = ? 
                AND datetime(timestamp) > datetime('now', '-' || ? || ' minutes')
            """, (src_ip, minutes))
            
            return cursor.fetchone()[0]

    def insert_correlation(self, correlation: Dict[str, Any]) -> int:
        """
        Insert a detected correlation/attack pattern
        
        Args:
            correlation: Dictionary with correlation details
            
        Returns:
            Correlation ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            details = json.dumps(correlation.get('details', {}))
            
            cursor.execute("""
                INSERT INTO correlations 
                (attack_type, src_ip, alert_count, unique_signatures, 
                 first_alert_time, last_alert_time, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                correlation.get('attack_type', ''),
                correlation.get('src_ip', ''),
                correlation.get('alert_count', 0),
                correlation.get('unique_signatures', 0),
                correlation.get('first_alert_time', None),
                correlation.get('last_alert_time', None),
                details
            ))
            
            conn.commit()
            return cursor.lastrowid

    def get_correlations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent correlation detections"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM correlations 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM alerts")
            total_alerts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT src_ip) FROM alerts")
            unique_ips = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM correlations")
            correlations = cursor.fetchone()[0]
            
            return {
                'total_alerts': total_alerts,
                'unique_ips': unique_ips,
                'correlations_detected': correlations
            }

    def clear_old_alerts(self, days: int = 7):
        """Delete alerts older than X days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM alerts 
                WHERE datetime(timestamp) < datetime('now', '-' || ? || ' days')
            """, (days,))
            
            conn.commit()

    def block_ip(self, ip_address: str, reason: str = 'Manual block by admin') -> bool:
        """
        Block an IP address
        
        Args:
            ip_address: IP to block
            reason: Reason for blocking
            
        Returns:
            True if successful, False if already blocked
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO blocked_ips (ip_address, reason)
                    VALUES (?, ?)
                """, (ip_address, reason))
                
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # IP already blocked
            return False

    def unblock_ip(self, ip_address: str) -> bool:
        """
        Unblock an IP address
        
        Args:
            ip_address: IP to unblock
            
        Returns:
            True if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM blocked_ips WHERE ip_address = ?
            """, (ip_address,))
            
            conn.commit()
            return cursor.rowcount > 0

    def is_ip_blocked(self, ip_address: str) -> bool:
        """
        Check if an IP is blocked
        
        Args:
            ip_address: IP to check
            
        Returns:
            True if blocked, False otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 1 FROM blocked_ips WHERE ip_address = ?
            """, (ip_address,))
            
            return cursor.fetchone() is not None

    def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get list of all blocked IPs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ip_address, reason, blocked_at FROM blocked_ips
                ORDER BY blocked_at DESC
            """)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
