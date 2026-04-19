from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import requests
import numpy as np
import time

app = FastAPI(title="InbutpowerfullFX AI Agent")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────
# FETCH DATA
# ──────────────────────────────────────────
def fetch_candles(symbol: str, timeframe: str, limit: int = 100):
    base = 3300
    candles = []
    t = int(time.time()) - limit * 900
    price = base

    for i in range(limit):
        change = np.random.randn() * 5
        open_p = price
        close_p = price + change
        high_p = max(open_p, close_p) + abs(np.random.randn() * 2)
        low_p  = min(open_p, close_p) - abs(np.random.randn() * 2)

        candles.append({
            "time": t + i * 900,
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low":  round(low_p, 2),
            "close":round(close_p, 2),
            "volume": round(abs(np.random.randn() * 1000), 2)
        })

        price = close_p

    return candles

# ──────────────────────────────────────────
# ANALYSIS
# ──────────────────────────────────────────
@app.get("/analyze")
def analyze(symbol: str = "XAUUSD", timeframe: str = "15M"):
    candles = fetch_candles(symbol, timeframe)

    last_price = candles[-1]["close"]

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "last_price": last_price,
        "signal": "⏳ WAIT & SEE",
        "entry": last_price,
        "sl": last_price + 5,
        "tp1": last_price - 5,
        "tp2": last_price - 10,
        "candles": candles
    }

# ──────────────────────────────────────────
# UI DASHBOARD
# ──────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>INBUTPOWERFULLFX AI</title>
    </head>
    <body style="background:black;color:white;text-align:center;font-family:sans-serif;">
        
        <h1>🚀 INBUTPOWERFULLFX AI</h1>
        <p>AI Trading System Active</p>

        <button onclick="loadSignal()" style="padding:10px 20px;font-size:16px;">
            🔥 Run AI Signal
        </button>

        <h2 id="result"></h2>

        <script>
        async function loadSignal(){
            const res = await fetch('/analyze');
            const data = await res.json();

            document.getElementById("result").innerHTML = `
                📊 SYMBOL: ${data.symbol} <br>
                💰 PRICE: ${data.last_price} <br>
                ⚡ SIGNAL: ${data.signal} <br>
                🎯 ENTRY: ${data.entry} <br>
                🛑 SL: ${data.sl} <br>
                🥇 TP1: ${data.tp1} <br>
                🥈 TP2: ${data.tp2}
            `;
        }
        </script>

        <br><br>
        <a href="/docs" style="color:cyan;">Open API Docs</a>

    </body>
    </html>
    """

# ──────────────────────────────────────────
# STATUS
# ──────────────────────────────────────────
@app.get("/status")
def status():
    return {"status": "RUNNING"}
