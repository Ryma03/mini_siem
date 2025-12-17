#!/usr/bin/env python3
"""
Mini SIEM Test Suite
Tests all components of the system
"""

import sys
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import DatabaseManager
from core.enricher import IPEnricher
from core.collector import MockAlertGenerator, SnortAlertParser
from core.correlator import CorrelationEngine


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_success(text):
    """Print success message"""
    print(f"✓ {text}")


def print_error(text):
    """Print error message"""
    print(f"✗ {text}")


def print_info(text):
    """Print info message"""
    print(f"→ {text}")


def test_database():
    """Test database functionality"""
    print_header("Testing Database Module")

    try:
        db = DatabaseManager()
        print_success("Database initialized")

        # Get stats
        stats = db.get_alert_stats()
        print_info(f"Current stats: {stats}")

        # Test alert insertion
        test_alert = {
            'signature': 'Test Alert',
            'src_ip': '192.168.1.100',
            'dst_ip': '10.0.0.1',
            'src_port': 54321,
            'dst_port': 443,
            'protocol': 'TCP',
            'severity': 'HIGH',
            'message': 'Test alert message',
            'enrichment': {
                'source': {
                    'country': 'Test',
                    'city': 'Lab',
                    'asn': 'AS12345'
                }
            }
        }

        alert_id = db.insert_alert(test_alert)
        print_success(f"Alert inserted with ID: {alert_id}")

        # Retrieve alert
        alerts = db.get_recent_alerts(limit=5)
        print_success(f"Retrieved {len(alerts)} recent alerts")

        return True

    except Exception as e:
        print_error(f"Database test failed: {str(e)}")
        return False


def test_enricher():
    """Test IP enrichment"""
    print_header("Testing IP Enrichment Module")

    try:
        enricher = IPEnricher(use_free_api=True)
        print_success("IP enricher initialized")

        # Test private IP
        print_info("Testing private IP...")
        private_enrichment = enricher.enrich_ip('192.168.1.1')
        assert private_enrichment['country'] == 'Private'
        print_success("Private IP enrichment works")

        # Test public IP (with cache)
        print_info("Testing public IP enrichment (first call - may take a few seconds)...")
        public_enrichment = enricher.enrich_ip('8.8.8.8')
        assert 'country' in public_enrichment
        print_success(f"Public IP enriched: {public_enrichment['country']}")

        # Test cache (second call should be instant)
        print_info("Testing cache (second call)...")
        start = time.time()
        cached_enrichment = enricher.enrich_ip('8.8.8.8')
        elapsed = time.time() - start
        assert elapsed < 0.1, "Cache not working efficiently"
        print_success(f"Cache working (response time: {elapsed:.4f}s)")

        return True

    except Exception as e:
        print_error(f"Enrichment test failed: {str(e)}")
        return False


def test_collector():
    """Test alert collection and parsing"""
    print_header("Testing Alert Collector Module")

    try:
        parser = SnortAlertParser()
        print_success("Parser initialized")

        # Test mock alert generation
        print_info("Generating mock alerts...")
        mock_alerts = MockAlertGenerator.generate_batch(count=5)
        assert len(mock_alerts) == 5
        print_success(f"Generated {len(mock_alerts)} mock alerts")

        # Test alert properties
        for alert in mock_alerts:
            assert 'signature' in alert
            assert 'src_ip' in alert
            assert 'dst_ip' in alert
            assert 'severity' in alert

        print_info(f"Sample alert: {mock_alerts[0]['signature']}")

        return True

    except Exception as e:
        print_error(f"Collector test failed: {str(e)}")
        return False


def test_correlator():
    """Test correlation engine"""
    print_header("Testing Correlation Engine")

    try:
        db = DatabaseManager()
        correlator = CorrelationEngine(db)
        print_success("Correlation engine initialized")

        # Insert test alerts to trigger correlation
        print_info("Inserting test alerts for correlation...")
        for i in range(6):
            alert = {
                'timestamp': '2025-12-11 12:00:' + f'{i:02d}',
                'signature': f'Test Signature {i % 2}',
                'src_ip': '192.168.1.50',
                'dst_ip': '10.0.0.1',
                'src_port': 54321 + i,
                'dst_port': 443,
                'protocol': 'TCP',
                'severity': 'HIGH',
                'message': f'Test alert {i}',
                'enrichment': {}
            }
            db.insert_alert(alert)

        print_success("Test alerts inserted")

        # Run correlation analysis
        print_info("Running correlation analysis...")
        correlations = correlator.analyze_alerts()
        print_success(f"Found {len(correlations)} correlations")

        if correlations:
            for corr in correlations:
                print_info(f"  - {corr['attack_type']} from {corr['src_ip']}")

        return True

    except Exception as e:
        print_error(f"Correlator test failed: {str(e)}")
        return False


def test_end_to_end():
    """End-to-end system test"""
    print_header("End-to-End System Test")

    try:
        db = DatabaseManager()
        enricher = IPEnricher(use_free_api=True)
        correlator = CorrelationEngine(db)

        print_info("Simulating alert flow...")

        # Generate alerts
        alerts = MockAlertGenerator.generate_batch(count=3)
        print_success(f"Generated {len(alerts)} alerts")

        # Process through system
        for alert in alerts:
            enriched = enricher.enrich_alert(alert)
            db.insert_alert(enriched)

        print_success("Alerts processed and stored")

        # Analyze correlations
        correlations = correlator.analyze_alerts()
        print_success(f"Correlation analysis complete ({len(correlations)} detections)")

        # Get stats
        stats = db.get_alert_stats()
        print_success(f"Final stats: {stats}")

        return True

    except Exception as e:
        print_error(f"End-to-end test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print_header("Mini SIEM Test Suite")

    tests = [
        ("Database Module", test_database),
        ("IP Enrichment", test_enricher),
        ("Alert Collection", test_collector),
        ("Correlation Engine", test_correlator),
        ("End-to-End System", test_end_to_end),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\nTests interrupted by user")
            sys.exit(1)
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")
            results.append((test_name, False))

    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")

    print_info(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print_success("All tests passed!")
        return 0
    else:
        print_error("Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
