#!/usr/bin/env python3
"""
Quick Start Script for Mini SIEM
Automated setup and testing
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Print welcome banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║          Mini SIEM - Quick Start Guide                       ║
    ║                                                              ║
    ║   Security Information and Event Management System           ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def check_python():
    """Check Python version"""
    print("[*] Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✓ Python {version.major}.{version.minor} found")
        return True
    else:
        print(f"✗ Python 3.10+ required (found {version.major}.{version.minor})")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("\n[*] Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])
        print("✓ Dependencies installed")
        return True
    except Exception as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def run_tests():
    """Run test suite"""
    print("\n[*] Running test suite...")
    try:
        subprocess.check_call([sys.executable, "test_suite.py"])
        print("✓ Tests completed")
        return True
    except subprocess.CalledProcessError:
        print("✗ Some tests failed")
        return False

def main():
    """Main quick start"""
    print_banner()
    
    # Check Python
    if not check_python():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Run tests
    print("\n[*] Would you like to run the test suite? (y/n) ", end="")
    if input().lower() == 'y':
        run_tests()
    
    # Show next steps
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    NEXT STEPS                                ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Option 1: Run with mock alerts (testing, no Snort needed)
    ─────────────────────────────────────────────────────────────
    Terminal 1:
    $ python siem_orchestrator.py --mock
    
    Terminal 2:
    $ python app/main.py
    
    Then open: http://localhost:5000
    
    
    Option 2: Run with real Snort (Linux only)
    ─────────────────────────────────────────────────────────────
    1. Install Snort:
       $ sudo apt-get install snort
    
    2. Configure Snort:
       $ sudo nano /etc/snort/snort.conf
    
    3. Create log directory:
       $ sudo mkdir -p /var/log/snort
       $ sudo chmod 777 /var/log/snort
    
    4. Start Snort:
       $ sudo snort -c /etc/snort/snort.conf -l /var/log/snort -A fast
    
    5. In another terminal, start SIEM:
       $ python siem_orchestrator.py
    
    6. In a third terminal, start web UI:
       $ python app/main.py
    
    
    Optional: Generate test alerts
    ─────────────────────────────────────────────────────────────
    $ nmap -sV localhost        # Network scanning alerts
    $ nmap -p22 localhost       # SSH port scan alerts
    
    
    Dashboard Access
    ─────────────────────────────────────────────────────────────
    URL: http://localhost:5000
    Pages:
      / - Main dashboard with statistics
      /alerts - All collected alerts
      /correlations - Detected attack patterns
      /search - Search and filter alerts
    
    
    API Endpoints
    ─────────────────────────────────────────────────────────────
    GET /api/alerts              - Get recent alerts (JSON)
    GET /api/alerts/ip/<ip>      - Alerts from specific IP
    GET /api/correlations        - Get detected patterns
    GET /api/stats               - System statistics
    GET /api/enrich-ip/<ip>      - Enrich IP information
    
    
    Documentation
    ─────────────────────────────────────────────────────────────
    See README.md for detailed documentation
    See mini_siem.log for system logs
    
    ╔══════════════════════════════════════════════════════════════╗
    ║             Setup complete! Good luck! 🚀                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

if __name__ == '__main__':
    main()
