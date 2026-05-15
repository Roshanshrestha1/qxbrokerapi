# Installation Guide for QxBroker API

## Quick Start (Recommended)

```bash
chmod +x run.sh
./run.sh
```

This automated script handles everything including the Python 3.13 compatibility issues.

## Manual Installation (If run.sh fails)

### Option 1: Using Conda/Mamba (Best for Python 3.13)

If you have conda or mamba installed:

```bash
# Create environment with Python 3.12 (more compatible)
conda create -n qxbroker python=3.12 -y
conda activate qxbroker

# Install dependencies from conda-forge
conda install -c conda-forge pandas numpy playwright -y

# Install Python packages
pip install fastapi uvicorn[standard] python-dotenv websockets aiohttp cloudscraper beautifulsoup4

# Install QxBroker client
pip install git+https://github.com/A11ksa/API-Quotex.git

# Install Playwright browsers
playwright install chromium

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Option 2: Downgrade to Python 3.11 or 3.12

Python 3.13 is very new and some packages don't have pre-built wheels yet.

**Ubuntu/Debian:**
```bash
sudo apt install python3.11 python3.11-venv python3.11-dev
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Option 3: Force Binary Installation

```bash
# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install only binary packages (no compilation)
pip install --only-binary=all fastapi uvicorn[standard] python-dotenv websockets aiohttp cloudscraper beautifulsoup4

# Install numpy and pandas with specific versions that have wheels
pip install --only-binary=all numpy==2.0.0 pandas==2.1.4 || \
pip install --prefer-binary numpy pandas

# Install playwright
pip install playwright
playwright install chromium

# Install QxBroker client
pip install git+https://github.com/A11ksa/API-Quotex.git

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Error: "Cannot set property backgroundColorNames"

This is a Node.js/Playwright display issue, not a real error. The script filters these messages automatically.

### Error: "Connection closed while reading from the driver"

Run: `playwright install chromium`

If that fails, try:
```bash
playwright install-deps chromium  # Linux only
playwright install chromium
```

### Error: pandas build failure with Python 3.13

Python 3.13 is too new for pandas 2.1.4. Solutions:
1. Use the updated `run.sh` script (installs pandas 2.2.0+)
2. Downgrade to Python 3.11 or 3.12
3. Use conda/mamba as shown above

### Error: Module not found after installation

Make sure you're in the virtual environment:
```bash
source venv/bin/activate
```

## Environment Setup

Create a `.env` file with your credentials:

```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

Required variables:
- `QX_EMAIL`: Your QxBroker email
- `QX_PASSWORD`: Your QxBroker password  
- `QX_ACCOUNT`: PRACTICE or REAL

## Verification

After installation, verify everything works:

```bash
# Test Playwright
python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright OK')"

# Test QxBroker client
python -c "from api_quotex import get_ssid; print('✅ QxBroker client OK')"

# Start API
uvicorn main:app --host 0.0.0.0 --port 8000
```

Visit http://localhost:8000/docs to see the API documentation.
