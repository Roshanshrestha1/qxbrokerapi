#!/bin/bash

# Alternative Installation Script for Python 3.13
# This script uses pre-built wheels and handles compatibility issues

set -e

echo "=========================================="
echo "  QxBroker API - Alternative Installer  "
echo "=========================================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "🐍 Detected Python $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo "⚠️  Python 3.13 detected - using compatibility mode"
    echo ""
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📥 Upgrading pip..."
pip install --upgrade pip -q

# Install packages with binary-only flag first
echo "📦 Installing core packages (binary only)..."
pip install --only-binary=:all: fastapi uvicorn[standard] python-dotenv websockets aiohttp beautifulsoup4 setuptools -q || \
pip install fastapi uvicorn[standard] python-dotenv websockets aiohttp beautifulsoup4 setuptools -q

# Install cloudscraper separately (has dependencies)
echo "📦 Installing cloudscraper..."
pip install cloudscraper -q || true

# Handle numpy and pandas based on Python version
if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo "📦 Installing numpy/pandas for Python 3.13..."
    # Try latest versions first
    pip install --pre numpy pandas -q 2>/dev/null || \
    pip install "numpy>=2.0.0" "pandas>=2.2.0" -q 2>/dev/null || \
    pip install numpy pandas --no-build-isolation -q 2>/dev/null || {
        echo "⚠️  Could not install pandas from PyPI"
        echo "💡 Recommendation: Use Python 3.11 or 3.12, or use conda"
        echo "   See INSTALL.md for alternative installation methods"
    }
else
    echo "📦 Installing numpy and pandas..."
    pip install numpy pandas -q
fi

# Install playwright
echo "📦 Installing Playwright..."
pip install playwright -q
playwright install chromium 2>&1 | grep -v "TypeError\|babelBundleImpl\|backgroundColorNames" || true

# Install system dependencies if on Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🔧 Installing system dependencies..."
    playwright install-deps chromium 2>&1 | grep -v "TypeError\|babelBundleImpl" || true
fi

# Install QxBroker client last
echo "📦 Installing QxBroker client library..."
pip install git+https://github.com/A11ksa/API-Quotex.git -q || {
    echo "⚠️  Could not install QxBroker client automatically"
    echo "💡 Try installing manually:"
    echo "   pip install git+https://github.com/A11ksa/API-Quotex.git"
}

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env (if not exists)"
echo "2. Edit .env with your QxBroker credentials"
echo "3. Run: ./run.sh"
echo ""
echo "Or start directly:"
echo "  source venv/bin/activate"
echo "  uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
