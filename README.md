# QxBroker Candle Data & Trading API

A clean, production-ready REST API for fetching real-time and historical candle data from QxBroker via WebSocket connection. Includes full trading functionality for placing CALL/PUT trades on DEMO or REAL accounts.

## Features

- **Real-time candle data** - Fetch live candles as they form
- **Historical data** - Get up to 24 hours of historical OHLCV data
- **Market sentiment** - Access real trader buy/sell percentages
- **Asset information** - List all available assets and payout rates
- **Account management** - Check balance, switch between DEMO/REAL accounts
- **Live trading** - Place CALL (UP) and PUT (DOWN) trades
- **Trade status** - Monitor open and closed trade positions
- **Secure authentication** - Session management with secure file permissions
- **Production ready** - Proper logging, error handling, and retry logic

## Quick Start

### Option 1: Using the Run Script (Recommended)

```bash
cd /workspace
./run.sh
```

The script will:
- Create `.env` file from template if missing
- Set up virtual environment
- Install all dependencies
- Install Playwright browsers
- Perform initial login to save session
- Start the API server

### Option 2: Manual Setup

#### 1. Configure Environment

Edit `.env` with your QxBroker credentials:

```env
QX_EMAIL=your_email@example.com
QX_PASSWORD=your_password
QX_ACCOUNT=PRACTICE  # or REAL
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium  # Linux only
```

#### 3. Run the API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or simply:
```bash
python main.py
```

#### 4. Access Documentation

Open your browser to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/

## API Endpoints

### Health & Status

| Endpoint | Description |
|----------|-------------|
| `GET /` | API health check |
| `GET /docs` | Swagger UI documentation |

### Account Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /balance` | GET | Get account balance |
| `GET /account/status` | GET | Full account status (type, balance, connection) |
| `POST /account/switch` | POST | Switch between DEMO and REAL accounts |

#### Account Status Example
```bash
curl http://localhost:8000/account/status
# Response: {"account_type": "DEMO", "is_demo": true, "connected": true, "balance": {...}}
```

#### Switch Account Example
```bash
curl -X POST "http://localhost:8000/account/switch?account_type=REAL"
# Response: {"account_type": "REAL", "is_demo": false, "balance": {...}, "status": "switched successfully"}
```

### Assets

| Endpoint | Description |
|----------|-------------|
| `GET /assets` | List all available assets |
| `GET /payouts` | Get payout percentages |

### Candles

| Endpoint | Description |
|----------|-------------|
| `GET /candles/{asset}` | Historical candles (1-24 hours) |
| `GET /candles/{asset}/latest` | Latest N candles (max 200) |
| `GET /candles/{asset}/max` | Maximum 200 candles |
| `GET /candles/{asset}/live` | Current forming candle |

### Price & Sentiment

| Endpoint | Description |
|----------|-------------|
| `GET /price/{asset}` | Latest tick price |
| `GET /sentiment/{asset}` | Market sentiment (% buy/sell) |

### Trading Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /trade/place` | POST | Place CALL/PUT trade |
| `GET /trade/status/{id}` | GET | Check trade status by ID |

#### Place Trade Example
```bash
# Place a $10 CALL (UP) trade on EURUSD for 60 seconds on DEMO account
curl -X POST "http://localhost:8000/trade/place?asset=EURUSD&direction=CALL&amount=10&duration=60&account_type=DEMO"

# Place a $25 PUT (DOWN) trade on BTCUSD for 5 minutes on REAL account
curl -X POST "http://localhost:8000/trade/place?asset=BTCUSD&direction=PUT&amount=25&duration=300&account_type=REAL"
```

**Trade Parameters:**
- `asset`: Asset symbol (e.g., 'EURUSD', 'BTCUSD_otc')
- `direction`: 'CALL' (UP) or 'PUT' (DOWN)
- `amount`: Trade amount in account currency
- `duration`: Trade duration in seconds (default: 60)
- `account_type`: 'DEMO' or 'REAL' (default: DEMO)

**Response:**
```json
{
  "success": true,
  "trade_id": "12345678",
  "asset": "EURUSD",
  "direction": "CALL",
  "amount": 10.0,
  "duration": 60,
  "account_type": "DEMO",
  "timestamp": 1234567890,
  "status": "open",
  "details": {...}
}
```

#### Check Trade Status Example
```bash
curl http://localhost:8000/trade/status/12345678
# Response: {"trade_id": "12345678", "status": "closed", "profit": 8.50, "payout": 18.50, ...}
```

## Usage Examples

### Get Historical Candles

```bash
# 2 hours of 1-minute candles for EURUSD
curl "http://localhost:8000/candles/EURUSD?period=60&hours=2"

# 15-minute candles for Bitcoin OTC
curl "http://localhost:8000/candles/BTCUSD_otc?period=900&hours=1"
```

### Get Latest Candles

```bash
# Last 50 candles
curl "http://localhost:8000/candles/EURUSD/latest?period=60&count=50"

# Maximum 200 candles
curl "http://localhost:8000/candles/EURUSD/max?period=60"
```

### Get Live Candle

```bash
# Current forming 1-minute candle
curl "http://localhost:8000/candles/EURUSD/live?period=60"
```

### Get Market Sentiment

```bash
curl "http://localhost:8000/sentiment/EURUSD"
# Response: {"asset": "EURUSD", "sentiment": {"buy": 62, "sell": 38}}
```

### Complete Trading Flow

```bash
# 1. Check account status
curl http://localhost:8000/account/status

# 2. Switch to REAL account (if needed)
curl -X POST "http://localhost:8000/account/switch?account_type=REAL"

# 3. Check current sentiment
curl http://localhost:8000/sentiment/EURUSD

# 4. Place a CALL trade based on bullish sentiment
curl -X POST "http://localhost:8000/trade/place?asset=EURUSD&direction=CALL&amount=10&duration=60"

# 5. Monitor trade status
curl http://localhost:8000/trade/status/12345678
```

## Docker Support

Build and run with Docker:

```bash
docker build -t qx-candle-api .
docker run -p 8000:8000 --env-file .env qx-candle-api
```

## Valid Parameters

### Asset Examples
- Forex: `EURUSD`, `GBPUSD`, `USDJPY`
- Crypto: `BTCUSD`, `ETHUSD`, `XAUUSD` (Gold)
- OTC variants: Add `_otc` suffix (e.g., `EURUSD_otc`)

### Period Options (seconds)
- `5` - 5 seconds
- `60` - 1 minute
- `300` - 5 minutes
- `900` - 15 minutes
- `3600` - 1 hour
- `86400` - 1 day

### Trade Directions
- `CALL` or `UP` - Bet that price will go up
- `PUT` or `DOWN` - Bet that price will go down

### Account Types
- `DEMO` or `PRACTICE` - Demo trading account
- `REAL` - Real money trading account

## Security Notes

- Session files are created with restricted permissions (owner read/write only)
- Credentials are loaded from environment variables only
- CORS is restricted to localhost by default
- Never commit your `.env` file to version control
- Use DEMO accounts for testing before trading with real money

## Disclaimer

Trading binary options involves significant risk and may not be suitable for all investors. This API is provided for educational and informational purposes only. Always trade responsibly and never invest more than you can afford to lose.

## License

MIT License
