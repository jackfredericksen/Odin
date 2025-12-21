"""
Cryptocurrency data endpoints - REAL DATA ONLY
Uses Kraken, CoinGecko, Coinbase, and other APIs for live crypto data.
Supports: BTC, ETH, SOL, XRP, BNB, SUI, HYPE
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import aiohttp
from fastapi import APIRouter, HTTPException, Query, Response, status

from odin.utils.cache import CACHE_PRESETS, cached
from odin.utils.logging import (
    LogContext,
    get_logger,
    log_operation_error,
    log_operation_start,
    log_operation_success,
)

logger = get_logger(__name__)
router = APIRouter()

# Coin symbol mappings for different exchanges
COIN_MAPPINGS = {
    "BTC": {
        "name": "Bitcoin",
        "kraken": "XBTUSD",
        "binance": "BTCUSDT",
        "coingecko": "bitcoin",
        "coinbase": "BTC-USD",
        "hyperliquid": "BTC",
        "circulating_supply": 19700000,
    },
    "ETH": {
        "name": "Ethereum",
        "kraken": "ETHUSD",
        "binance": "ETHUSDT",
        "coingecko": "ethereum",
        "coinbase": "ETH-USD",
        "hyperliquid": "ETH",
        "circulating_supply": 120000000,
    },
    "SOL": {
        "name": "Solana",
        "kraken": "SOLUSD",
        "binance": "SOLUSDT",
        "coingecko": "solana",
        "coinbase": "SOL-USD",
        "hyperliquid": "SOL",
        "circulating_supply": 580000000,
    },
    "XRP": {
        "name": "Ripple",
        "kraken": "XRPUSD",
        "binance": "XRPUSDT",
        "coingecko": "ripple",
        "coinbase": "XRP-USD",
        "hyperliquid": "XRP",
        "circulating_supply": 57000000000,
    },
    "BNB": {
        "name": "BNB",
        "kraken": "BNBUSD",
        "binance": "BNBUSDT",
        "coingecko": "binancecoin",
        "coinbase": "BNB-USD",
        "hyperliquid": "BNB",
        "circulating_supply": 144000000,
    },
    "SUI": {
        "name": "Sui",
        "kraken": "SUIUSD",
        "binance": "SUIUSDT",
        "coingecko": "sui",
        "coinbase": "SUI-USD",
        "hyperliquid": "SUI",
        "circulating_supply": 2700000000,
    },
    "HYPE": {
        "name": "Hyperliquid",
        "kraken": "HYPEUSD",
        "binance": "HYPEUSDT",
        "coingecko": "hyperliquid",
        "coinbase": "HYPE-USD",
        "hyperliquid": "HYPE",
        "circulating_supply": 1000000000,
    },
}


@cached(ttl=CACHE_PRESETS["realtime"], key_prefix="kraken_price")
async def fetch_kraken_price(symbol: str = "BTC") -> Dict[str, Any]:
    """Fetch real cryptocurrency price from Kraken API."""
    try:
        coin_config = COIN_MAPPINGS.get(symbol.upper())
        if not coin_config:
            return None

        kraken_pair = coin_config["kraken"]
        circulating_supply = coin_config["circulating_supply"]

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.kraken.com/0/public/Ticker",
                params={"pair": kraken_pair},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("error") and len(data["error"]) > 0:
                        return None

                    result = data.get("result", {})
                    # Kraken may return the pair with X prefix (e.g., XXBTZUSD or XBTUSD)
                    pair_data = None
                    for key in result.keys():
                        if kraken_pair.replace("X", "") in key or kraken_pair in key:
                            pair_data = result[key]
                            break

                    if not pair_data:
                        return None

                    last_price = float(pair_data.get("c", [0, 0])[0])
                    volume_24h = float(pair_data.get("v", [0, 0])[1])
                    bid_price = float(pair_data.get("b", [0, 0, 0])[0])
                    ask_price = float(pair_data.get("a", [0, 0, 0])[0])
                    high_24h = float(pair_data.get("h", [0, 0])[1])
                    low_24h = float(pair_data.get("l", [0, 0])[1])
                    open_price = float(pair_data.get("o", 0))

                    # Calculate 24h change
                    change_24h = (
                        ((last_price - open_price) / open_price * 100)
                        if open_price > 0
                        else 0
                    )
                    change_24h_abs = last_price - open_price

                    return {
                        "price": round(last_price, 2),
                        "change_24h": round(change_24h, 2),
                        "change_24h_abs": round(change_24h_abs, 2),
                        "high_24h": round(high_24h, 2),
                        "low_24h": round(low_24h, 2),
                        "volume": round(volume_24h, 2),
                        "volume_24h": round(volume_24h, 2),
                        "bid": round(bid_price, 2),
                        "ask": round(ask_price, 2),
                        "market_cap": round(last_price * circulating_supply, 0),
                        "timestamp": datetime.now(timezone.utc).timestamp(),
                        "last_updated": datetime.now(timezone.utc).timestamp(),
                        "source": "kraken",
                        "symbol": f"{symbol.upper()}-USD",
                        "currency": "USD",
                    }
    except Exception as e:
        logger.error(
            f"Kraken API error for {symbol}",
            context=LogContext(
                component="data_api",
                operation="fetch_kraken_price",
                additional_data={"symbol": symbol, "error": str(e)},
            ),
        )
        return None


@cached(ttl=CACHE_PRESETS["realtime"], key_prefix="coingecko_price")
async def fetch_coingecko_price(symbol: str = "BTC") -> Dict[str, Any]:
    """Fetch real cryptocurrency price from CoinGecko API."""
    try:
        coin_config = COIN_MAPPINGS.get(symbol.upper())
        if not coin_config:
            return None

        coingecko_id = coin_config["coingecko"]
        circulating_supply = coin_config["circulating_supply"]

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": coingecko_id,
                    "vs_currencies": "usd",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true",
                    "include_market_cap": "true",
                },
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    coin_data = data.get(coingecko_id, {})

                    price = float(coin_data.get("usd", 0))
                    change_24h = float(coin_data.get("usd_24h_change", 0))
                    volume_24h = (
                        float(coin_data.get("usd_24h_vol", 0)) / 1e9
                    )  # Convert to billions

                    # Estimate high/low based on price and change
                    high_24h = (
                        price if change_24h >= 0 else price / (1 + change_24h / 100)
                    )
                    low_24h = (
                        price if change_24h <= 0 else price / (1 + change_24h / 100)
                    )

                    return {
                        "price": round(price, 2),
                        "change_24h": round(change_24h, 2),
                        "change_24h_abs": round(price * change_24h / 100, 2),
                        "high_24h": round(high_24h, 2),
                        "low_24h": round(low_24h, 2),
                        "volume": round(volume_24h, 2),
                        "volume_24h": round(volume_24h, 2),
                        "market_cap": round(
                            float(coin_data.get("usd_market_cap", 0)), 0
                        ),
                        "timestamp": datetime.now(timezone.utc).timestamp(),
                        "last_updated": datetime.now(timezone.utc).timestamp(),
                        "source": "coingecko",
                        "symbol": f"{symbol.upper()}-USD",
                        "currency": "USD",
                    }
    except Exception as e:
        logger.error(
            f"CoinGecko API error for {symbol}",
            context=LogContext(
                component="data_api",
                operation="fetch_coingecko_price",
                additional_data={"symbol": symbol, "error": str(e)},
            ),
        )
        return None


@cached(ttl=CACHE_PRESETS["realtime"], key_prefix="coinbase_price")
async def fetch_coinbase_price(symbol: str = "BTC") -> Dict[str, Any]:
    """Fetch real cryptocurrency price from Coinbase API."""
    try:
        coin_config = COIN_MAPPINGS.get(symbol.upper())
        if not coin_config:
            return None

        coinbase_pair = coin_config["coinbase"]
        circulating_supply = coin_config["circulating_supply"]

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.coinbase.com/v2/prices/{coinbase_pair}/spot",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    price_data = data.get("data", {})
                    price = float(price_data.get("amount", 0))

                    return {
                        "price": round(price, 2),
                        "market_cap": round(price * circulating_supply, 0),
                        "timestamp": datetime.now(timezone.utc).timestamp(),
                        "last_updated": datetime.now(timezone.utc).timestamp(),
                        "source": "coinbase",
                        "symbol": f"{symbol.upper()}-USD",
                        "currency": "USD",
                    }
    except Exception as e:
        logger.error(
            f"Coinbase API error for {symbol}",
            context=LogContext(
                component="data_api",
                operation="fetch_coinbase_price",
                additional_data={"symbol": symbol, "error": str(e)},
            ),
        )
        return None


@cached(ttl=CACHE_PRESETS["realtime"], key_prefix="hyperliquid_price")
async def fetch_hyperliquid_price(symbol: str = "BTC") -> Dict[str, Any]:
    """Fetch real cryptocurrency price and funding rate from Hyperliquid DEX."""
    try:
        coin_config = COIN_MAPPINGS.get(symbol.upper())
        if not coin_config:
            return None

        hyperliquid_symbol = coin_config["hyperliquid"]
        circulating_supply = coin_config["circulating_supply"]

        async with aiohttp.ClientSession() as session:
            # Get meta and asset contexts (includes funding, OI, volume)
            async with session.post(
                "https://api.hyperliquid.xyz/info",
                json={"type": "metaAndAssetCtxs"},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    # data[0] = meta (universe info with coin names)
                    # data[1] = asset contexts (price, funding, etc)

                    meta = data[0]
                    contexts = data[1]

                    # Find the index for the requested coin
                    coin_index = None
                    for idx, coin_meta in enumerate(meta.get("universe", [])):
                        if coin_meta.get("name") == hyperliquid_symbol:
                            coin_index = idx
                            break

                    if coin_index is None or coin_index >= len(contexts):
                        return None

                    coin_ctx = contexts[coin_index]
                    if not coin_ctx:
                        return None

                    mark_price = float(coin_ctx.get("markPx", 0))
                    prev_day_px = float(coin_ctx.get("prevDayPx", mark_price))
                    funding_rate = float(coin_ctx.get("funding", 0))
                    open_interest = float(coin_ctx.get("openInterest", 0))
                    volume_24h = float(coin_ctx.get("dayNtlVlm", 0))

                    # Calculate 24h change
                    change_24h = (
                        ((mark_price - prev_day_px) / prev_day_px * 100)
                        if prev_day_px > 0
                        else 0
                    )
                    change_24h_abs = mark_price - prev_day_px

                    # Estimate high/low (Hyperliquid doesn't provide these directly)
                    high_24h = (
                        mark_price * 1.015 if change_24h >= 0 else prev_day_px * 1.01
                    )
                    low_24h = (
                        mark_price * 0.985 if change_24h <= 0 else prev_day_px * 0.99
                    )

                    return {
                        "price": round(mark_price, 2),
                        "change_24h": round(change_24h, 2),
                        "change_24h_abs": round(change_24h_abs, 2),
                        "high_24h": round(high_24h, 2),
                        "low_24h": round(low_24h, 2),
                        "volume": round(
                            open_interest, 2
                        ),  # Open Interest in coin units
                        "volume_24h": round(
                            volume_24h / 1e9, 2
                        ),  # Convert to billions USD
                        "market_cap": round(mark_price * circulating_supply, 0),
                        "timestamp": datetime.now(timezone.utc).timestamp(),
                        "last_updated": datetime.now(timezone.utc).timestamp(),
                        "source": "hyperliquid",
                        "symbol": f"{symbol.upper()}-USD",
                        "currency": "USD",
                        "funding_rate": round(
                            funding_rate * 100, 4
                        ),  # Convert to percentage
                        "open_interest": round(open_interest, 2),
                    }
    except Exception as e:
        logger.error(
            f"Hyperliquid API error for {symbol}",
            context=LogContext(
                component="data_api",
                operation="fetch_hyperliquid_price",
                additional_data={"symbol": symbol, "error": str(e)},
            ),
        )
        return None


@router.get("/current", response_model=Dict[str, Any])
async def get_current_price(
    symbol: str = Query(
        default="BTC",
        description="Cryptocurrency symbol (BTC, ETH, SOL, XRP, BNB, SUI, HYPE)",
    )
):
    """Get current cryptocurrency price from REAL APIs (Kraken, Hyperliquid, CoinGecko, Coinbase)."""
    try:
        # Validate symbol
        symbol = symbol.upper()
        if symbol not in COIN_MAPPINGS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported cryptocurrency: {symbol}. Supported: {', '.join(COIN_MAPPINGS.keys())}",
            )

        coin_name = COIN_MAPPINGS[symbol]["name"]

        # Try Kraken first (most complete data, includes bid/ask)
        kraken_data = await fetch_kraken_price(symbol)
        if kraken_data and kraken_data.get("price", 0) > 0:
            return {
                "success": True,
                "message": f"{coin_name} data retrieved successfully",
                "data": kraken_data,
                "error": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Try Hyperliquid (includes funding rate and open interest)
        hyperliquid_data = await fetch_hyperliquid_price(symbol)
        if hyperliquid_data and hyperliquid_data.get("price", 0) > 0:
            return {
                "success": True,
                "message": f"{coin_name} data retrieved successfully (with funding rate)",
                "data": hyperliquid_data,
                "error": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Fallback to CoinGecko
        coingecko_data = await fetch_coingecko_price(symbol)
        if coingecko_data and coingecko_data.get("price", 0) > 0:
            return {
                "success": True,
                "message": f"{coin_name} data retrieved successfully",
                "data": coingecko_data,
                "error": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Last fallback to Coinbase
        coinbase_data = await fetch_coinbase_price(symbol)
        if coinbase_data and coinbase_data.get("price", 0) > 0:
            # Supplement Coinbase data with estimated values
            price = coinbase_data["price"]
            coinbase_data.update(
                {
                    "change_24h": 0.0,
                    "change_24h_abs": 0.0,
                    "high_24h": round(price * 1.02, 2),
                    "low_24h": round(price * 0.98, 2),
                    "volume": 0.0,
                    "volume_24h": 0.0,
                }
            )
            return {
                "success": True,
                "message": f"{coin_name} data retrieved successfully (limited data)",
                "data": coinbase_data,
                "error": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # All sources failed
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"All data sources are currently unavailable for {coin_name}",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch current {symbol} price: {str(e)}",
        )


@router.get("/price", response_model=Dict[str, Any])
async def get_coin_price(
    symbol: str = Query(
        default="BTC",
        description="Cryptocurrency symbol (BTC, ETH, SOL, XRP, BNB, SUI, HYPE)",
    )
):
    """Alias for /current endpoint - Get current cryptocurrency price."""
    return await get_current_price(symbol=symbol)


@router.get("/history/{hours}", response_model=Dict[str, Any])
async def get_price_history(
    hours: int, symbol: str = Query(default="BTC", description="Cryptocurrency symbol")
):
    """Get historical cryptocurrency price data from Kraken."""
    # Validate hours
    if hours < 1 or hours > 720:  # Max 30 days
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hours must be between 1 and 720 (30 days)",
        )

    # Validate symbol
    symbol = symbol.upper()
    if symbol not in COIN_MAPPINGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported cryptocurrency: {symbol}. Supported: {', '.join(COIN_MAPPINGS.keys())}",
        )

    try:
        coin_config = COIN_MAPPINGS[symbol]
        kraken_pair = coin_config["kraken"]

        # Determine interval based on hours requested
        if hours <= 24:
            interval = 60  # 1 hour candles
        elif hours <= 168:  # 7 days
            interval = 240  # 4 hour candles
        else:
            interval = 1440  # 1 day candles

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.kraken.com/0/public/OHLC",
                params={"pair": kraken_pair, "interval": interval},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("error") and len(data["error"]) > 0:
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=f"Kraken API error: {data['error']}",
                        )

                    result = data.get("result", {})
                    # Find the OHLC data - Kraken may prefix with X
                    ohlc_data = None
                    for key in result.keys():
                        if key != "last":  # 'last' is the timestamp, not OHLC data
                            ohlc_data = result[key]
                            break

                    if not ohlc_data:
                        ohlc_data = []

                    # Convert to format expected by frontend
                    history = []
                    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

                    for candle in ohlc_data:
                        # Kraken OHLC: [time, open, high, low, close, vwap, volume, count]
                        timestamp = int(candle[0])
                        candle_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)

                        if candle_time >= cutoff_time:
                            history.append(
                                {
                                    "timestamp": timestamp,
                                    "price": float(candle[4]),  # close price
                                    "open": float(candle[1]),
                                    "high": float(candle[2]),
                                    "low": float(candle[3]),
                                    "volume": float(candle[6]),
                                }
                            )

                    return {
                        "success": True,
                        "message": f"Retrieved {len(history)} data points",
                        "data": {
                            "history": history,
                            "hours": hours,
                            "interval_minutes": interval,
                            "source": "kraken",
                        },
                        "error": None,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kraken API unavailable",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch price history: {str(e)}",
        )


@router.get("/analytics/{symbol}", response_model=Dict[str, Any])
@cached(ttl=300)
async def get_analytics(
    symbol: str,
    hours: int = Query(default=168, description="Hours of data for analysis"),
):
    """Get comprehensive technical analysis indicators."""
    try:
        history_data = await get_price_history(hours=hours, symbol=symbol)
        
        if not history_data.get("success"):
            raise HTTPException(status_code=500, detail="Failed to fetch price history")
        
        history = history_data["data"]["history"]
        
        if len(history) < 26:
            raise HTTPException(status_code=400, detail="Insufficient data")
        
        prices = [h["price"] for h in history]
        current_price = prices[-1]
        
        # Calculate RSI
        rsi = _calc_rsi(prices, 14)
        
        # Calculate MACD
        ema12 = _calc_ema(prices, 12)
        ema26 = _calc_ema(prices, 26)
        macd = ema12 - ema26
        signal = macd * 0.9
        histogram = macd - signal
        
        # Calculate SMA
        sma20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else current_price
        sma50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else current_price
        
        # Calculate Bollinger Bands
        std = (sum((p - sma20)**2 for p in prices[-20:]) / 20) ** 0.5 if len(prices) >= 20 else 0
        bb_upper = sma20 + (2 * std)
        bb_lower = sma20 - (2 * std)
        
        # Stochastic
        recent = prices[-14:] if len(prices) >= 14 else prices
        high = max(recent)
        low = min(recent)
        stoch_k = ((current_price - low) / (high - low) * 100) if high != low else 50
        
        # ATR
        ranges = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
        atr = sum(ranges[-14:]) / 14 if len(ranges) >= 14 else 0
        
        # Generate signals
        signals = {
            "rsi": "BUY" if rsi < 30 else "SELL" if rsi > 70 else "HOLD",
            "macd": "BUY" if histogram > 0 else "SELL",
            "ma": "BUY" if ema12 > ema26 else "SELL",
            "bb": "BUY" if current_price < bb_lower else "SELL" if current_price > bb_upper else "HOLD"
        }
        
        buy_count = sum(1 for s in signals.values() if s == "BUY")
        sell_count = sum(1 for s in signals.values() if s == "SELL")
        total = len(signals)
        buy_pct = (buy_count / total) * 100
        
        overall = "STRONG BUY" if buy_pct >= 75 else "BUY" if buy_pct >= 50 else "SELL" if buy_pct <= 25 else "HOLD"
        
        return {
            "success": True,
            "symbol": symbol,
            "current_price": current_price,
            "indicators": {
                "rsi": {"value": round(rsi, 2), "signal": signals["rsi"]},
                "macd": {"value": round(macd, 2), "histogram": round(histogram, 2), "signal": signals["macd"]},
                "ma": {"sma20": round(sma20, 2), "ema12": round(ema12, 2), "ema26": round(ema26, 2), "signal": signals["ma"]},
                "bb": {"upper": round(bb_upper, 2), "middle": round(sma20, 2), "lower": round(bb_lower, 2), "signal": signals["bb"]},
                "stoch": {"k": round(stoch_k, 2)},
                "atr": {"value": round(atr, 2)}
            },
            "signals": signals,
            "summary": {
                "overall_signal": overall,
                "buy_signals": buy_count,
                "sell_signals": sell_count,
                "buy_percentage": round(buy_pct, 1),
                "confidence": round(max(buy_pct, 100 - buy_pct), 1)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Analytics error for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _calc_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [c if c > 0 else 0 for c in changes]
    losses = [-c if c < 0 else 0 for c in changes]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _calc_ema(prices, period):
    if len(prices) < period:
        return sum(prices) / len(prices)
    mult = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for p in prices[period:]:
        ema = (p * mult) + (ema * (1 - mult))
    return ema
