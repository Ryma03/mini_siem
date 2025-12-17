#!/usr/bin/env python3
"""
Generate test data for correlation detection
"""

from core.database import DatabaseManager
from core.correlator import CorrelationEngine
from datetime import datetime, timedelta
import random
import sys

def generate_test_correlations():
    """Generate alerts that will trigger correlation patterns"""
    db = DatabaseManager()
    
    print("🔄 Generating correlated alert data...")
    
    # Pattern 1: High volume attack from single IP
    test_ip_1 = '192.168.50.100'
    signatures = ['Port Scan', 'SQL Injection', 'Buffer Overflow', 'Malware C&C', 'DDoS Attack']
    
    print(f"\n📊 Creating 25 alerts from {test_ip_1} (High Volume Attack)...")
    for i in range(25):
        alert = {
            'timestamp': (datetime.now() - timedelta(minutes=random.randint(0, 8))).strftime('%Y-%m-%d %H:%M:%S'),
            'signature': random.choice(signatures),
            'src_ip': test_ip_1,
            'dst_ip': '10.0.0.1',
            'protocol': random.choice(['TCP', 'UDP']),
            'severity': random.choice(['HIGH', 'HIGH', 'MEDIUM']),
            'details': f'Alert {i+1} for correlation test'
        }
        db.insert_alert(alert)
    print(f"   ✓ {25} alerts created")
    
    # Pattern 2: Multi-signature attack from another IP
    test_ip_2 = '203.0.113.50'
    print(f"\n📊 Creating 18 alerts from {test_ip_2} (Multi-Signature Attack)...")
    for i in range(18):
        alert = {
            'timestamp': (datetime.now() - timedelta(minutes=random.randint(0, 8))).strftime('%Y-%m-%d %H:%M:%S'),
            'signature': signatures[i % len(signatures)],  # Cycle through different signatures
            'src_ip': test_ip_2,
            'dst_ip': '10.0.0.2',
            'protocol': 'TCP',
            'severity': random.choice(['MEDIUM', 'HIGH']),
            'details': f'Multi-sig alert {i+1}'
        }
        db.insert_alert(alert)
    print(f"   ✓ {18} alerts created")
    
    # Analyze and report
    print("\n🔍 Analyzing for correlations...")
    engine = CorrelationEngine(db)
    correlations = engine.analyze_alerts()
    
    print(f"\n✅ Correlations detected: {len(correlations)}")
    if correlations:
        for i, corr in enumerate(correlations, 1):
            print(f"\n   Pattern {i}:")
            print(f"   Type: {corr.get('attack_type')}")
            print(f"   Source IP: {corr.get('src_ip')}")
            print(f"   Alert Count: {corr.get('alert_count')}")
            print(f"   Unique Signatures: {corr.get('unique_signatures', 'N/A')}")
    else:
        print("   No correlations detected yet")
    
    print("\n🎯 Done! Refresh /correlations page to see results.")
    return len(correlations)

if __name__ == '__main__':
    try:
        count = generate_test_correlations()
        sys.exit(0 if count > 0 else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
