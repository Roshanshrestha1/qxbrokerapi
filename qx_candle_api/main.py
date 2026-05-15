"""
QxBroker Candle Data API Server
================================
Clean, production-ready API for fetching real-time and historical candle data
from QxBroker via WebSocket connection. Includes trading functionality for
placing CALL/PUT trades on DEMO or REAL accounts.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8000

Environment Variables:
    QX_EMAIL     - QxBroker account email
    QX_PASSWORD  - QxBroker account password
    QX_ACCOUNT   - PRACTICE or REAL (default: PRACTICE)

Endpoints:
    GET /                       - API health check
    GET /docs                   - Swagger UI documentation
    GET /balance                - Account balance
    GET /account/status         - Full account status (type, balance, connection)
    POST /account/switch        - Switch between DEMO and REAL accounts
    GET /assets                 - Available trading assets
    GET /payouts                - Asset payout percentages
    GET /candles/{asset}        - Historical OHLCV candles
    GET /candles/{asset}/latest - Latest N candles
    GET /candles/{asset}/max    - Maximum 200 candles
    GET /candles/{asset}/live   - Current forming candle
    GET /price/{asset}          - Latest tick price
    GET /sentiment/{asset}      - Market sentiment (buy/sell %)
    POST /trade/place           - Place CALL/PUT trade
    GET /trade/status/{id}      - Check trade status
"""

import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from qx_client import (
    connect_client,
    fetch_historical_candles,
    fetch_latest_candles,
    fetch_realtime_candle,
    fetch_realtime_price,
    fetch_sentiment,
    fetch_balance,
    fetch_all_assets,
    fetch_payouts,
    place_trade,
    get_trade_status,
    switch_account,
    get_account_status,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# -------------------------------------------------------
# Application Lifecycle Management
# -------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize WebSocket connection on startup."""
    logger.info("Starting QxBroker Candle API...")
    await connect_client()
    logger.info("API server ready to accept requests")
    yield
    logger.info("Shutting down API server...")


app = FastAPI(
    title="QxBroker Candle Data API",
    description="Production API for real-time and historical candle data from QxBroker",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration - restrict to localhost for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_methods=["GET"],
    allow_headers=["*"],
    allow_credentials=False,
)


# -------------------------------------------------------
# API ENDPOINTS
# -------------------------------------------------------


@app.get("/", tags=["Health"])
async def root():
    """API health check and information endpoint."""
    return {
        "status": "running",
        "service": "QxBroker Candle Data API",
        "version": "1.0.0",
        "documentation": "/docs",
    }


@app.get("/balance", tags=["Account"])
async def get_balance():
    """
    Retrieve current account balance.
    
    Returns balance information for the authenticated account.
    """
    try:
        return await fetch_balance()
    except Exception as e:
        logger.error(f"Balance fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assets", tags=["Assets"])
async def get_assets():
    """
    Get all available trading assets categorized by type.
    
    Returns assets separated into normal and OTC (Over-The-Counter) categories.
    """
    try:
        assets = await fetch_all_assets()

        # Categorize assets
        normal = sorted([a for a in assets.keys() if not a.endswith("_otc")])
        otc = sorted([a for a in assets.keys() if a.endswith("_otc")])

        return {
            "total": len(assets),
            "normal_count": len(normal),
            "otc_count": len(otc),
            "normal": normal,
            "otc": otc,
            "all": sorted(assets.keys()),
        }
    except Exception as e:
        logger.error(f"Assets fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/payouts", tags=["Assets"])
async def get_payouts():
    """
    Get payout percentages for all available assets.
    
    Indicates which assets are currently open for trading and their payout rates.
    """
    try:
        return await fetch_payouts()
    except Exception as e:
        logger.error(f"Payouts fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/candles/{asset}", tags=["Candles"])
async def get_candles(
    asset: str,
    period: int = Query(
        default=60,
        description="Candle period in seconds: 5,15,30,60,300,900,3600,86400",
    ),
    hours: int = Query(
        default=1, 
        description="Hours of historical data to fetch (1-24)",
        ge=1, 
        le=24
    ),
):
    """
    Fetch historical OHLCV candles from QxBroker.
    
    **Asset Examples:**
    - EURUSD, GBPUSD, USDJPY, XAUUSD, BTCUSD
    - Add _otc suffix for OTC: EURUSD_otc
    
    **Period Examples (seconds):**
    - 5, 60 (1min), 300 (5min), 900 (15min), 3600 (1hr), 86400 (1day)
    
    **Example Request:** `/candles/EURUSD?period=60&hours=2`
    """
    valid_periods = [5, 10, 15, 30, 60, 120, 180, 240, 300, 600, 900, 1800, 3600, 14400, 86400]
    if period not in valid_periods:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid period. Must be one of: {valid_periods}"
        )

    try:
        candles = await fetch_historical_candles(
            asset=asset.upper(), hours=hours, period=period
        )
        return {
            "asset": asset.upper(),
            "period": period,
            "hours": hours,
            "count": len(candles),
            "candles": candles,
        }
    except Exception as e:
        logger.error(f"Candles fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/candles/{asset}/latest", tags=["Candles"])
async def get_latest_candles(
    asset: str,
    period: int = Query(default=60, description="Candle period in seconds"),
    count: int = Query(default=100, description="Number of candles (1-200)", ge=1, le=200),
):
    """
    Fetch latest N candles (maximum 200).
    
    **Example:** `/candles/EURUSD/latest?period=60&count=50`
    """
    try:
        candles = await fetch_latest_candles(
            asset=asset.upper(), count=count, period=period
        )
        return {
            "asset": asset.upper(),
            "period": period,
            "count": len(candles),
            "candles": candles,
        }
    except Exception as e:
        logger.error(f"Latest candles fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/candles/{asset}/max", tags=["Candles"])
async def get_max_candles(
    asset: str,
    period: int = Query(default=60, description="Candle period in seconds"),
):
    """
    Fetch maximum allowed candles (200) at once.
    
    This endpoint returns up to 200 candles, which is the broker's limit.
    
    **Example:** `/candles/EURUSD/max?period=60`
    """
    try:
        candles = await fetch_latest_candles(
            asset=asset.upper(), count=200, period=period
        )
        return {
            "asset": asset.upper(),
            "period": period,
            "count": len(candles),
            "candles": candles,
        }
    except Exception as e:
        logger.error(f"Max candles fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/candles/{asset}/live", tags=["Candles"])
async def get_live_candle(
    asset: str,
    period: int = Query(default=60, description="Candle period in seconds"),
):
    """
    Get the current live candle being formed in real-time.
    
    **Example:** `/candles/EURUSD/live?period=60`
    """
    try:
        candle = await fetch_realtime_candle(asset=asset.upper(), period=period)
        return {"asset": asset.upper(), "period": period, "candle": candle}
    except Exception as e:
        logger.error(f"Live candle fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/price/{asset}", tags=["Price"])
async def get_price(
    asset: str,
    period: int = Query(default=60, description="Candle period in seconds"),
):
    """
    Get the latest tick price for an asset.
    
    **Example:** `/price/EURUSD`
    """
    try:
        price = await fetch_realtime_price(asset=asset.upper(), period=period)
        return {"asset": asset.upper(), "data": price}
    except Exception as e:
        logger.error(f"Price fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sentiment/{asset}", tags=["Sentiment"])
async def get_sentiment(asset: str):
    """
    Get real-time market sentiment (% of traders buying vs selling).
    
    Returns the percentage of traders currently buying vs selling the asset.
    
    **Example:** `/sentiment/EURUSD`
    **Response:** `{"buy": 62, "sell": 38}`
    """
    try:
        sentiment = await fetch_sentiment(asset.upper())
        return {"asset": asset.upper(), "sentiment": sentiment}
    except Exception as e:
        logger.error(f"Sentiment fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/account/status", tags=["Account"])
async def account_status():
    """
    Get current account status including type (DEMO/REAL), balance, and connection state.
    
    Returns comprehensive account information.
    """
    try:
        return await get_account_status()
    except Exception as e:
        logger.error(f"Account status fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/account/switch", tags=["Account"])
async def switch_trading_account(account_type: str = Query(..., description="DEMO, PRACTICE, or REAL")):
    """
    Switch between DEMO/PRACTICE and REAL trading accounts.
    
    **Parameters:**
    - account_type: 'DEMO', 'PRACTICE', or 'REAL'
    
    **Example:** `/account/switch?account_type=REAL`
    """
    try:
        return await switch_account(account_type)
    except Exception as e:
        logger.error(f"Account switch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trade/place", tags=["Trading"])
async def trade_place(
    asset: str = Query(..., description="Asset symbol (e.g., EURUSD, BTCUSD_otc)"),
    direction: str = Query(..., description="CALL (UP) or PUT (DOWN)"),
    amount: float = Query(..., description="Trade amount in account currency"),
    duration: int = Query(default=60, description="Trade duration in seconds"),
    account_type: str = Query(default="DEMO", description="DEMO or REAL account")
):
    """
    Place a CALL (UP) or PUT (DOWN) trade.
    
    **Parameters:**
    - asset: Asset symbol (e.g., 'EURUSD', 'BTCUSD_otc')
    - direction: 'CALL' (UP) or 'PUT' (DOWN)
    - amount: Trade amount
    - duration: Trade duration in seconds (default: 60)
    - account_type: 'DEMO' or 'REAL' (default: DEMO)
    
    **Example:** `/trade/place?asset=EURUSD&direction=CALL&amount=10&duration=60&account_type=DEMO`
    
    **Response:** Trade ID, status, and details
    """
    try:
        result = await place_trade(
            asset=asset.upper(),
            direction=direction.upper(),
            amount=amount,
            duration=duration,
            account_type=account_type
        )
        return result
    except ValueError as e:
        logger.error(f"Invalid trade parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Trade placement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trade/status/{trade_id}", tags=["Trading"])
async def trade_status(trade_id: str):
    """
    Get the current status of a trade by its ID.
    
    Returns trade status, profit/loss, and closing information if available.
    
    **Example:** `/trade/status/12345678`
    """
    try:
        return await get_trade_status(trade_id)
    except Exception as e:
        logger.error(f"Trade status check failed for {trade_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Application entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
