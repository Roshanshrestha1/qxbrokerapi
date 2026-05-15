#!/bin/bash

# QxBroker API - Complete Setup and Run Script
# This script sets up the environment, installs Playwright browsers,
# performs login to save cookies/session, and starts the API server.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  QxBroker Candle API - Setup & Run    ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found!${NC}"
    echo ""
    
    if [ -f ".env.example" ]; then
        echo -e "${BLUE}📋 Copying .env.example to .env...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env with your QxBroker credentials!${NC}"
        echo ""
        echo "Open .env and set:"
        echo "  QX_EMAIL=your_email@example.com"
        echo "  QX_PASSWORD=your_password"
        echo "  QX_ACCOUNT=PRACTICE (or REAL)"
        echo ""
        read -p "Press Enter after you've updated .env..."
    else
        echo -e "${RED}❌ No .env.example found either!${NC}"
        echo "Please create a .env file with your credentials."
        exit 1
    fi
fi

# Validate .env has required variables
echo -e "${BLUE}🔍 Checking environment configuration...${NC}"
source .env 2>/dev/null || true

if [ -z "$QX_EMAIL" ] || [ -z "$QX_PASSWORD" ]; then
    echo -e "${RED}❌ Missing required environment variables!${NC}"
    echo ""
    echo "Edit .env and ensure these are set:"
    echo "  QX_EMAIL=your_email@example.com"
    echo "  QX_PASSWORD=your_password"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Environment configured${NC}"
echo ""

# Check Python version
echo -e "${BLUE}🐍 Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed!${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
    echo ""
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
    echo ""
fi

# Activate virtual environment
echo -e "${BLUE}🔌 Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Install/upgrade pip
echo -e "${BLUE}📥 Upgrading pip...${NC}"
pip install --upgrade pip --quiet
echo -e "${GREEN}✅ Pip upgraded${NC}"
echo ""

# Install requirements (with retry for pandas build issues)
echo -e "${BLUE}📦 Installing dependencies...${NC}"
echo "Note: This may take a few minutes..."

# Try installing with --no-binary for pandas if build fails
if ! pip install -r requirements.txt --quiet 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Standard installation had issues, trying alternative method...${NC}"
    
    # Install packages one by one to isolate issues
    pip install fastapi uvicorn[standard] python-dotenv websockets aiohttp cloudscraper beautifulsoup4 setuptools --quiet
    
    # Install numpy first (required by pandas)
    echo "Installing numpy..."
    pip install "numpy>=1.26.4" --quiet
    
    # Install latest pandas (Python 3.13 compatible)
    echo "Installing pandas..."
    # Try installing from PyPI first, then try with --pre for pre-release wheels
    if ! pip install "pandas>=2.2.0" --quiet 2>/dev/null; then
        echo "Trying pre-release pandas for Python 3.13..."
        pip install --pre pandas --quiet || pip install pandas --no-build-isolation --quiet || true
    fi
    
    # Install playwright separately
    echo "Installing playwright..."
    pip install playwright --quiet
    
    # Install the QxBroker library last
    echo "Installing QxBroker client..."
    pip install git+https://github.com/A11ksa/API-Quotex.git --quiet || true
    
    echo -e "${GREEN}✅ Dependencies installed (some may use fallback versions)${NC}"
else
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi
echo ""

# Install Playwright browsers
echo -e "${BLUE}🌐 Installing Playwright browsers (this may take a while)...${NC}"
playwright install chromium 2>&1 | grep -v "TypeError\|babelBundleImpl\|backgroundColorNames" || true
echo -e "${GREEN}✅ Playwright browsers installed${NC}"
echo ""

# Install Playwright system dependencies (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${BLUE}🔧 Installing Playwright system dependencies...${NC}"
    playwright install-deps chromium 2>&1 | grep -v "TypeError\|babelBundleImpl" || true
    echo -e "${GREEN}✅ System dependencies installed${NC}"
    echo ""
fi

# Create session directory if needed
SESSION_DIR="$(dirname "$(readlink -f "$0")")"
if [ ! -d "$SESSION_DIR" ]; then
    mkdir -p "$SESSION_DIR"
fi

echo -e "${BLUE}🔐 Performing initial login to save session...${NC}"
echo "This will open a browser window for authentication."
echo ""

# Run a quick login script to save session
cat > /tmp/qx_login.py << 'EOF'
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

async def perform_login():
    try:
        from api_quotex import get_ssid
        
        email = os.getenv("QX_EMAIL")
        password = os.getenv("QX_PASSWORD")
        
        if not email or not password:
            print("❌ Error: QX_EMAIL or QX_PASSWORD not set")
            return False
        
        print("🔑 Attempting login...")
        success, ssid_info = await get_ssid(email=email, password=password)
        
        if success:
            print("✅ Login successful! Session saved.")
            account_type = os.getenv("QX_ACCOUNT", "PRACTICE").upper()
            ssid = ssid_info.get("live") if account_type == "REAL" else ssid_info.get("ssid")
            print(f"🎫 Session ID obtained: {ssid[:20]}..." if ssid else "🎫 Session ID obtained")
            return True
        else:
            print("❌ Login failed. Check your credentials.")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        print("\nTroubleshooting tips:")
        print("  1. Check your email/password in .env")
        print("  2. Make sure Playwright browsers are installed")
        print("  3. Try running: playwright install chromium")
        return False

if __name__ == "__main__":
    result = asyncio.run(perform_login())
    sys.exit(0 if result else 1)
EOF

python /tmp/qx_login.py
LOGIN_RESULT=$?

rm -f /tmp/qx_login.py

if [ $LOGIN_RESULT -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Initial login did not complete successfully.${NC}"
    echo "The API will attempt to login when it starts."
    echo "Make sure your credentials are correct in .env"
    echo ""
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${BLUE}🚀 Starting QxBroker API Server...${NC}"
echo ""
echo "📡 API will be available at:"
echo "   http://localhost:8000"
echo ""
echo "📚 API Documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the API server
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
