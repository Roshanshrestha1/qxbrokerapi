# QxBroker Candle Data API

A clean, production-ready REST API for fetching real-time and historical candle data from QxBroker via WebSocket connection.

## Features

- **Real-time candle data** - Fetch live candles as they form
- **Historical data** - Get up to 24 hours of historical OHLCV data
- **Market sentiment** - Access real trader buy/sell percentages
- **Asset information** - List all available assets and payout rates
- **Account balance** - Check your account balance
- **Secure authentication** - Session management with secure file permissions
- **Production ready** - Proper logging, error handling, and retry logic

## Quick Start

### 1. Clone and Setup

```bash
cd qx_candle_api
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` with your QxBroker credentials:

```env
QX_EMAIL=your_email@example.com
QX_PASSWORD=your_password
QX_ACCOUNT=PRACTICE  # or REAL
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Run the API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or simply:
```bash
python main.py
```

### 5. Access Documentation

Open your browser to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/

## API Endpoints

### Health & Status

| Endpoint | Description |
|----------|-------------|
| `GET /` | API health check |
| `GET /docs` | Swagger UI documentation |

### Account

| Endpoint | Description |
|----------|-------------|
| `GET /balance` | Get account balance |

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

## Security Notes

- Session files are created with restricted permissions (owner read/write only)
- Credentials are loaded from environment variables only
- CORS is restricted to localhost by default
- Never commit your `.env` file to version control

## License

MIT License
