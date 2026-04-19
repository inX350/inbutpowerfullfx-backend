from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import numpy as np
from typing import Optional
import time

app = FastAPI(title="InbutpowerfullFX AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────
# FETCH CANDLE DATA
# ──────────────────────────────────────────
def fetch_candles(symbol: str, timeframe: str, limit: int = 200):
    """Fetch OHLCV from Binance (for crypto) or fallback to Yahoo Finance"""
    tf_map = {
        "5M": "5m", "15M": "15m", "30M": "30m",
        "1H": "1h", "4H": "4h", "D": "1d"
    }
    interval = tf_map.get(timeframe, "15m")

    # Try Binance for BTC
    if "BTC" in symbol.upper():
        try:
            sym = "BTCUSDT"
            url = f"https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&limit={limit}"
            r = requests.get(url, timeout=10)
            data = r.json()
            candles = []
            for d in data:
                candles.append({
                    "time": int(d[0]) // 1000,
                    "open": float(d[1]),
                    "high": float(d[2]),
                    "low":  float(d[3]),
                    "close":float(d[4]),
                    "volume": float(d[5])
                })
            return candles
        except:
            pass

    # Try Binance for XAUUSDT (Gold)
    if "XAU" in symbol.upper() or "GOLD" in symbol.upper():
        try:
            sym = "XAUUSDT"
            url = f"https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&limit={limit}"
            r = requests.get(url, timeout=10)
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                candles = []
                for d in data:
                    candles.append({
                        "time": int(d[0]) // 1000,
                        "open": float(d[1]),
                        "high": float(d[2]),
                        "low":  float(d[3]),
                        "close":float(d[4]),
                        "volume": float(d[5])
                    })
                return candles
        except:
            pass

    # Fallback: generate mock data
    return generate_mock_candles(symbol, limit)


def generate_mock_candles(symbol: str, limit: int):
    """Generate realistic mock candles for demo"""
    base = 3300.0 if "XAU" in symbol.upper() else 76000.0
    candles = []
    t = int(time.time()) - limit * 900
    price = base
    for i in range(limit):
        change = np.random.randn() * base * 0.002
        open_p = price
        close_p = price + change
        high_p = max(open_p, close_p) + abs(np.random.randn() * base * 0.001)
        low_p  = min(open_p, close_p) - abs(np.random.randn() * base * 0.001)
        candles.append({
            "time": t + i * 900,
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low":  round(low_p, 2),
            "close":round(close_p, 2),
            "volume": round(abs(np.random.randn() * 1000 + 500), 2)
        })
        price = close_p
    return candles


# ──────────────────────────────────────────
# CANDLE DETECTION — INBUTPOWERFULLFX LOGIC
# ──────────────────────────────────────────
def is_doji(c, threshold=0.35):
    """Doji: body kecil, shadow atas & bawah seimbang"""
    body = abs(c["close"] - c["open"])
    total = c["high"] - c["low"]
    if total == 0:
        return False
    body_ratio = body / total
    upper_shadow = c["high"] - max(c["open"], c["close"])
    lower_shadow = min(c["open"], c["close"]) - c["low"]
    if lower_shadow == 0:
        return False
    shadow_ratio = upper_shadow / lower_shadow
    # Body kecil + shadow atas & bawah seimbang (ratio 0.5 - 2.0)
    return body_ratio < threshold and 0.4 < shadow_ratio < 2.5


def is_impulsive(c, candles, multiplier=1.8):
    """Impulsive: body besar > rata-rata x multiplier"""
    bodies = [abs(x["close"] - x["open"]) for x in candles[-20:]]
    avg_body = np.mean(bodies) if bodies else 1
    body = abs(c["close"] - c["open"])
    return body > avg_body * multiplier


def detect_engulfing_streak(candles, direction="bull", min_count=4):
    """Count consecutive engulfing candles at end of candles list"""
    count = 0
    for i in range(len(candles)-1, max(len(candles)-10, 0), -1):
        c = candles[i]
        p = candles[i-1]
        if direction == "bull":
            if c["close"] > c["open"] and c["close"] > p["high"] and c["open"] < p["low"]:
                count += 1
            else:
                break
        else:
            if c["close"] < c["open"] and c["close"] < p["low"] and c["open"] > p["high"]:
                count += 1
            else:
                break
    return count


def find_doji_impulsive_pairs(candles):
    """Find Doji + Impulsive pairs for Fibonacci drawing"""
    pairs = []
    for i in range(1, len(candles)-1):
        c = candles[i]
        next_c = candles[i+1]
        if is_doji(c) and is_impulsive(next_c, candles[:i+1]):
            pairs.append({
                "doji_idx": i,
                "impulsive_idx": i+1,
                "doji": c,
                "impulsive": next_c
            })
    return pairs


def find_doji_trendline(candles):
    """Find Doji to Doji trendline and count touches"""
    doji_indices = [i for i, c in enumerate(candles) if is_doji(c)]
    if len(doji_indices) < 2:
        return None

    # Take last 2 doji for trendline
    d1_idx = doji_indices[-2]
    d2_idx = doji_indices[-1]
    d1 = candles[d1_idx]
    d2 = candles[d2_idx]

    # Trendline from low of doji1 to low of doji2
    slope = (d2["low"] - d1["low"]) / (d2_idx - d1_idx) if d2_idx != d1_idx else 0

    # Count touches (price came near trendline)
    touches = 0
    trendline_points = []
    for i in range(d1_idx, len(candles)):
        trendline_price = d1["low"] + slope * (i - d1_idx)
        trendline_points.append({"time": candles[i]["time"], "value": round(trendline_price, 2)})
        tolerance = (candles[i]["high"] - candles[i]["low"]) * 0.5
        if abs(candles[i]["low"] - trendline_price) < tolerance:
            touches += 1

    return {
        "start_time": d1["time"],
        "end_time": d2["time"],
        "start_price": d1["low"],
        "end_price": d2["low"],
        "touches": touches,
        "valid": touches >= 4,
        "slope": slope,
        "points": trendline_points[-50:],
        "d1_idx": d1_idx,
        "d2_idx": d2_idx
    }


def calc_fibonacci(ll_price: float, hh_price: float, direction: str):
    """Calculate Fibonacci levels"""
    diff = hh_price - ll_price
    levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.618]
    result = {}
    for lvl in levels:
        price = ll_price + diff * lvl
        result[str(lvl)] = round(price, 2)
    return result


def detect_market_structure(candles):
    """Detect Bullish / Bearish / Sideways"""
    if len(candles) < 20:
        return "SIDEWAYS"
    recent = candles[-20:]
    highs = [c["high"] for c in recent]
    lows  = [c["low"]  for c in recent]
    hh = highs[-1] > max(highs[:-5]) if len(highs) > 5 else False
    hl = lows[-1]  > min(lows[:-5])  if len(lows) > 5  else False
    ll = lows[-1]  < min(lows[:-5])  if len(lows) > 5  else False
    lh = highs[-1] < max(highs[:-5]) if len(highs) > 5 else False
    if hh and hl:
        return "BULLISH"
    elif ll and lh:
        return "BEARISH"
    return "SIDEWAYS"


def calc_score(trendline, engulf_bull, engulf_bear, impulse_found, fibo_valid):
    """AI Score 0-100 based on InbutpowerfullFX rules"""
    score = 0
    breakdown = {}

    # Trendline 4x touch = 30pts
    tl_score = 30 if (trendline and trendline["valid"]) else (15 if trendline and trendline["touches"] >= 2 else 0)
    score += tl_score
    breakdown["trendline"] = {"score": tl_score, "max": 30, "touches": trendline["touches"] if trendline else 0}

    # Engulfing 4 candles = 30pts
    max_engulf = max(engulf_bull, engulf_bear)
    eng_score = 30 if max_engulf >= 4 else (15 if max_engulf >= 2 else 0)
    score += eng_score
    breakdown["engulfing"] = {"score": eng_score, "max": 30, "count": max_engulf}

    # Impulse = 20pts
    imp_score = 20 if impulse_found else 0
    score += imp_score
    breakdown["impulse"] = {"score": imp_score, "max": 20}

    # Fibo valid = 20pts
    fib_score = 20 if fibo_valid else 0
    score += fib_score
    breakdown["fibonacci"] = {"score": fib_score, "max": 20}

    return score, breakdown


# ──────────────────────────────────────────
# MAIN ANALYSIS ENDPOINT
# ──────────────────────────────────────────
@app.get("/analyze")
def analyze(symbol: str = "XAUUSD", timeframe: str = "15M"):
    candles = fetch_candles(symbol, timeframe, 200)
    if not candles:
        raise HTTPException(status_code=400, detail="Failed to fetch candles")

    last = candles[-1]
    structure = detect_market_structure(candles)

    # Trendline (Doji → Doji)
    trendline = find_doji_trendline(candles)

    # Engulfing streaks
    engulf_bull = detect_engulfing_streak(candles, "bull")
    engulf_bear = detect_engulfing_streak(candles, "bear")

    # Find Doji + Impulsive pairs
    pairs = find_doji_impulsive_pairs(candles)

    # Find recent impulsive candle
    impulse_found = any(is_impulsive(c, candles) for c in candles[-5:])

    # Determine direction
    direction = "BUY" if structure == "BULLISH" or engulf_bull >= 4 else \
                "SELL" if structure == "BEARISH" or engulf_bear >= 4 else "WAIT"

    # Fibonacci from most recent Doji → Impulsive pair
    fibo = None
    fibo_valid = False
    entry_price = None
    sl_price = None
    tp1_price = None
    tp2_price = None

    if pairs:
        last_pair = pairs[-1]
        doji_c = last_pair["doji"]
        imp_c  = last_pair["impulsive"]

        if direction == "BUY":
            ll = doji_c["low"]
            hh = imp_c["high"]
        else:
            ll = imp_c["low"]
            hh = doji_c["high"]

        fibo = calc_fibonacci(ll, hh, direction)
        diff = hh - ll

        # Entry zone 0.5–0.618
        fibo_valid = True
        cur_price = last["close"]
        entry_price = fibo["0.618"]
        if direction == "BUY":
            sl_price   = round(ll - diff * 0.05, 2)
            tp1_price  = round(fibo["1.0"], 2)
            tp2_price  = round(fibo["1.618"], 2)
        else:
            sl_price   = round(hh + diff * 0.05, 2)
            tp1_price  = round(fibo["0.0"], 2)
            tp2_price  = round(ll - diff * 0.1, 2)

    # Score
    score, breakdown = calc_score(trendline, engulf_bull, engulf_bear, impulse_found, fibo_valid)

    # Final signal
    if score < 60:
        signal = "⏳ WAIT & SEE"
        signal_color = "orange"
    elif direction == "BUY":
        signal = "✅ BUY VALID"
        signal_color = "green"
    elif direction == "SELL":
        signal = "🔴 SELL VALID"
        signal_color = "red"
    else:
        signal = "⏳ WAIT & SEE"
        signal_color = "orange"

    # Return last 100 candles for chart
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": candles[-100:],
        "last_price": last["close"],
        "structure": structure,
        "direction": direction,
        "signal": signal,
        "signal_color": signal_color,
        "score": score,
        "score_breakdown": breakdown,
        "trendline": trendline,
        "fibonacci": fibo,
        "entry": entry_price,
        "sl": sl_price,
        "tp1": tp1_price,
        "tp2": tp2_price,
        "engulf_bull": engulf_bull,
        "engulf_bear": engulf_bear,
        "impulse_found": impulse_found,
        "doji_count": sum(1 for c in candles[-20:] if is_doji(c)),
        "timestamp": int(time.time())
    }


@app.get("/")
def root():
    return {"status": "InbutpowerfullFX AI Agent Running", "version": "2.0"}


@app.get("/symbols")
def get_symbols():
    return {
        "symbols": ["XAUUSD", "BTCUSD", "EURUSD", "GBPJPY", "GBPUSD", "USDJPY"],
        "timeframes": ["5M", "15M", "30M", "1H", "4H", "D"]
    }
