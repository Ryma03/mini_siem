#!/bin/bash

# Mini SIEM Installation Script for Ubuntu/Debian

echo "======================================"
echo "Mini SIEM Installation Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ] && [ "$1" != "--no-sudo" ]; then 
   print_error "This script requires sudo privileges"
   echo "Run: sudo bash install.sh"
   exit 1
fi

print_status "Starting installation..."

# Update package lists
print_status "Updating package lists..."
apt-get update > /dev/null 2>&1

# Install Python 3 and pip
print_status "Installing Python 3..."
apt-get install -y python3 python3-pip python3-venv > /dev/null 2>&1

# Install Snort
print_status "Installing Snort IDS..."
apt-get install -y snort > /dev/null 2>&1

# Create Snort log directory
print_status "Setting up Snort directories..."
mkdir -p /var/log/snort
chmod 777 /var/log/snort

# Create Python virtual environment
print_status "Creating Python virtual environment..."
cd /opt/mini-siem 2>/dev/null || mkdir -p /opt/mini-siem
cd /opt/mini-siem
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -q -r requirements.txt

print_status "Installation complete!"
echo ""
echo "======================================"
echo "Next steps:"
echo "======================================"
echo ""
echo "1. Configure Snort (if not already done):"
echo "   sudo nano /etc/snort/snort.conf"
echo ""
echo "2. Generate test alerts:"
echo "   nmap -sV localhost"
echo ""
echo "3. Start Mini SIEM:"
echo "   # Option A: With mock alerts (for testing)"
echo "   python siem_orchestrator.py --mock"
echo ""
echo "   # Option B: With real Snort alerts"
echo "   python siem_orchestrator.py"
echo ""
echo "4. In another terminal, start web interface:"
echo "   cd /opt/mini-siem"
echo "   source venv/bin/activate"
echo "   python app/main.py"
echo ""
echo "5. Access dashboard:"
echo "   http://localhost:5000"
echo ""
echo "======================================"

print_status "Installation successful!"
