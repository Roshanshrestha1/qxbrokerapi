"""
QxBroker Client - Clean API-only client for candle data fetching.
All bot-related functionality removed. Focus on reliable WebSocket connection
and candle data retrieval via FastAPI endpoints.
"""

import asyncio
import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------
# Configuration Constants
# -------------------------------------------------------
MAX_RETRIES = 3
RETRY_DELAY = 2
SESSION_FILE_MODE = 0o600  # Secure file permissions (owner read/write only)
REQUEST_TIMEOUT = 30  # Seconds for API requests

# -------------------------------------------------------
# Singleton client — one connection shared across the API
# -------------------------------------------------------
_client = None
_ssid: Optional[str] = None
_connection_lock = asyncio.Lock()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def get_ssid() -> str:
    """
    Get SSID from QxBroker - tries existing session first, then fresh login.
    
    Returns:
        str: Session ID for API authentication
        
    Raises:
        ValueError: If credentials are missing
        Exception: If login fails
    """
    global _ssid

    session_file = os.path.join(os.path.dirname(__file__), "session.json")

    if _ssid is None:
        from api_quotex import get_ssid as playwright_get_ssid

        email = os.getenv("QX_EMAIL")
        password = os.getenv("QX_PASSWORD")

        # Validate credentials exist before proceeding
        if not email or not password:
            raise ValueError("QX_EMAIL and QX_PASSWORD must be set in environment variables")

        logger.info("Initializing QxBroker session...")

        # Try existing session first for efficiency
        if os.path.exists(session_file):
            logger.info("Attempting to restore existing session...")
            try:
                from api_quotex import get_ssid as validate_ssid

                success, ssid_info = await validate_ssid(email=email, password=password)
                if success:
                    account_type = os.getenv("QX_ACCOUNT", "PRACTICE").upper()
                    _ssid = ssid_info.get("live") if account_type == "REAL" else ssid_info.get("ssid")
                    
                    if _ssid:
                        logger.info(f"Session restored successfully")
                        return _ssid
            except Exception as e:
                logger.warning(f"Session restoration failed: {e}")

        # Perform fresh login
        logger.info("Performing fresh login...")
        success, ssid_info = await playwright_get_ssid(email=email, password=password)

        if not success:
            raise Exception("Failed to authenticate with QxBroker")

        account_type = os.getenv("QX_ACCOUNT", "PRACTICE").upper()
        _ssid = ssid_info.get("live") if account_type == "REAL" else ssid_info.get("ssid")

        if _ssid:
            logger.info("Authentication successful")
            # Secure session file permissions
            if os.path.exists(session_file):
                try:
                    os.chmod(session_file, SESSION_FILE_MODE)
                except Exception as e:
                    logger.warning(f"Could not secure session file: {e}")
        else:
            logger.error("Authentication failed - no SSID received")

    return _ssid or ""


async def get_client():
    """
    Get or create the singleton QxBroker client instance.
    Uses async lock to prevent race conditions during initialization.
    
    Returns:
        AsyncQuotexClient: Connected client instance
    """
    global _client

    async with _connection_lock:
        if _client is None:
            from api_quotex import AsyncQuotexClient

            ssid = await get_ssid()
            is_demo = os.getenv("QX_ACCOUNT", "PRACTICE").upper() == "PRACTICE"

            logger.info(f"Initializing client (demo={is_demo})")

            _client = AsyncQuotexClient(ssid=ssid, is_demo=is_demo)

    return _client


async def connect_client():
    """
    Establish WebSocket connection to QxBroker.
    Called once at API startup with retry logic.
    
    Returns:
        AsyncQuotexClient: Connected client
        
    Raises:
        ConnectionError: If connection fails after all retries
    """
    client = await get_client()

    logger.info("Establishing WebSocket connection...")
    
    for attempt in range(MAX_RETRIES):
        try:
            connected = await client.connect()
            logger.info(f"Connection attempt {attempt + 1}/{MAX_RETRIES}: {'success' if connected else 'failed'}")
            
            if connected:
                logger.info("WebSocket connection established")
                return client
            
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY}s...")
                await asyncio.sleep(RETRY_DELAY)
                
        except Exception as e:
            logger.error(f"Connection attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
    
    raise ConnectionError("Failed to connect after all retries")


async def ensure_connected():
    """
    Verify client connection status and return client instance.
    
    Returns:
        AsyncQuotexClient: Active client instance
    """
    global _client
    
    if _client is None:
        return await get_client()
    
    return _client


# -------------------------------------------------------
# CANDLE DATA FETCHERS - API Endpoints Support
# -------------------------------------------------------


async def fetch_historical_candles(
    asset: str, 
    hours: int = 1, 
    period: int = 60
) -> List[Dict[str, Any]]:
    """
    Fetch historical OHLCV candles from QxBroker.
    
    Args:
        asset: Asset symbol (e.g., 'EURUSD', 'BTCUSD_otc')
        hours: Number of hours of history (1-24)
        period: Candle period in seconds
        
    Returns:
        List of candle dictionaries with OHLCV data
    """
    client = await ensure_connected()
    num_candles = max(1, min((hours * 3600) // period, 200))  # Clamp to broker limit
    
    candles = await client.get_candles(asset, period, num_candles)
    
    result = []
    for c in candles:
        result.append({
            "time": int(c.timestamp.timestamp()) if hasattr(c.timestamp, "timestamp") else c.timestamp,
            "open": float(c.open),
            "high": float(c.high),
            "low": float(c.low),
            "close": float(c.close),
            "volume": float(c.volume) if hasattr(c, "volume") else 0.0,
        })
    
    return result


async def fetch_latest_candles(
    asset: str, 
    count: int = 200, 
    period: int = 60
) -> List[Dict[str, Any]]:
    """
    Fetch latest N candles (max 200 due to broker limits).
    
    Args:
        asset: Asset symbol
        count: Number of candles to fetch (clamped to 200)
        period: Candle period in seconds
        
    Returns:
        List of candle dictionaries
    """
    client = await ensure_connected()
    count = max(1, min(count, 200))  # Enforce broker limit
    
    candles = await client.get_candles(asset, period, count)
    
    result = []
    for c in candles:
        result.append({
            "time": int(c.timestamp.timestamp()) if hasattr(c.timestamp, "timestamp") else c.timestamp,
            "open": float(c.open),
            "high": float(c.high),
            "low": float(c.low),
            "close": float(c.close),
            "volume": float(c.volume) if hasattr(c, "volume") else 0.0,
        })
    
    return result


async def fetch_realtime_candle(asset: str, period: int = 60) -> List[Dict[str, Any]]:
    """Fetch the current live candle being formed."""
    return await fetch_latest_candles(asset, 1, period)


async def fetch_realtime_price(asset: str, period: int = 60) -> Optional[Dict[str, Any]]:
    """
    Get latest tick price for an asset.
    
    Returns:
        Dictionary with price and timestamp, or None if unavailable
    """
    candles = await fetch_latest_candles(asset, 1, period)
    if candles:
        return {"price": candles[0]["close"], "time": candles[0]["time"]}
    return None


async def fetch_sentiment(asset: str) -> Dict[str, Any]:
    """
    Fetch market sentiment (% buy vs sell).
    
    Returns:
        Dictionary with buy/sell percentages
    """
    client = await ensure_connected()
    return client.get_sentiment(asset)


async def fetch_balance() -> Dict[str, Any]:
    """
    Get current account balance.
    
    Returns:
        Balance information dictionary
    """
    client = await ensure_connected()
    return await client.get_balance()


async def fetch_all_assets() -> Dict[str, Any]:
    """
    Get all available trading assets.
    
    Returns:
        Dictionary of available assets
    """
    client = await ensure_connected()
    assets = await client.get_available_assets()
    return assets if assets else {}


async def fetch_payouts() -> Dict[str, Any]:
    """
    Get payout percentages for all assets.
    
    Returns:
        Dictionary mapping assets to payout percentages
    """
    client = await ensure_connected()
    return await client.get_assets_and_payouts()
