#!/bin/bash

# QxBroker API - Complete Setup and Run Script
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  QxBroker Candle API - Setup & Run    ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found!${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env from example${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  EDIT .env with your credentials before running!${NC}"
        echo "   Set: QX_EMAIL, QX_PASSWORD"
        exit 0
    fi
fi

# Validate credentials
source .env 2>/dev/null || true
if [ -z "$QX_EMAIL" ] || [ -z "$QX_PASSWORD" ] || [[ "$QX_EMAIL" == "your"* ]]; then
    echo -e "${RED}❌ Please edit .env with real credentials${NC}"
    echo "   Required: QX_EMAIL, QX_PASSWORD"
    exit 1
fi
echo -e "${GREEN}✅ Environment configured${NC}"
echo ""

# Create/activate venv
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Upgrade pip quietly
echo -e "${BLUE}📥 Upgrading pip...${NC}"
pip install --upgrade pip -q

# Install dependencies with fallback for Python 3.13
echo -e "${BLUE}📦 Installing dependencies...${NC}"

# Try to install pandas first with newer version for Python 3.13
if python3 --version 2>&1 | grep -q "3.13"; then
    echo "   Installing Python 3.13 compatible packages..."
    pip install pandas>=2.2.0 numpy>=1.26.0 -q 2>/dev/null || true
fi

# Install main requirements
pip install -r requirements.txt -q 2>&1 | grep -v "Successfully installed" || true
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Install Playwright browsers
echo -e "${BLUE}🌐 Installing Playwright browsers...${NC}"
playwright install chromium 2>&1 | grep -v "Cannot set property" || {
    playwright install chromium --force 2>/dev/null || echo "   ⚠️  Browser install had warnings"
}
echo -e "${GREEN}✅ Playwright ready${NC}"
echo ""

# Initial login
echo -e "${BLUE}🔐 Performing initial login...${NC}"
python3 << 'PYEOF'
import asyncio
import os
import sys
sys.path.insert(0, os.getcwd())

async def login():
    try:
        from qx_client import QxClient
        client = QxClient()
        email = os.getenv('QX_EMAIL')
        password = os.getenv('QX_PASSWORD')
        is_demo = os.getenv('QX_ACCOUNT', 'PRACTICE').upper() != 'REAL'
        
        print(f"   Email: {email}")
        print(f"   Account: {'DEMO' if is_demo else 'REAL'}")
        
        success = await client.login(email=email, password=password, is_demo=is_demo)
        if success:
            print("✅ Login successful!")
        else:
            print("⚠️  Login failed - will retry on first API call")
    except Exception as e:
        print(f"⚠️  Login error: {str(e)[:100]}")
        print("   Will retry on first API call")

asyncio.run(login())
PYEOF
echo ""

# Start server
echo -e "${GREEN}🚀 Starting API server...${NC}"
echo "   📍 http://0.0.0.0:8000"
echo "   📖 Docs: http://localhost:8000/docs"
echo -e "${BLUE}========================================${NC}"
echo ""
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
