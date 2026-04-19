from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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
# MOCK DATA (SIMULASI MARKET)
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
            "time": int(t + i * 900),  # FIX penting
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
        "signal_color": "orange",
        "entry": last_price,
        "sl": last_price + 5,
        "tp1": last_price - 5,
        "tp2": last_price - 10,
        "candles": candles
    }

# ──────────────────────────────────────────
# DASHBOARD UI (FINAL FIXED)
# ──────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>INBUTPOWERFULLFX AI</title>
    <script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
</head>

<body style="margin:0;background:#0f172a;color:white;font-family:sans-serif;">

    <h1 style="text-align:center;">🚀 INBUTPOWERFULLFX AI DASHBOARD</h1>

    <div id="chart" style="height:400px;"></div>

    <div style="text-align:center;margin-top:20px;">
        <button onclick="loadData()" style="padding:10px 20px;font-size:16px;">
            🔥 Load AI Signal
        </button>
    </div>

    <div id="signal" style="text-align:center;margin-top:20px;font-size:18px;"></div>

<script>
const chart = LightweightCharts.createChart(document.getElementById('chart'), {
    layout: { background: { color: '#0f172a' }, textColor: '#DDD' },
    grid: { vertLines: { color: '#222' }, horzLines: { color: '#222' } },
    width: window.innerWidth,
    height: 400
});

const candleSeries = chart.addCandlestickSeries();

// RESPONSIVE FIX
window.addEventListener('resize', () => {
    chart.resize(window.innerWidth, 400);
});

async function loadData() {
    const res = await fetch('/analyze');
    const data = await res.json();

    const candles = data.candles.map(c => ({
        time: Number(c.time), // FIX WAJIB
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close
    }));

    candleSeries.setData(candles);
    chart.timeScale().fitContent(); // FIX TAMBAHAN

    document.getElementById("signal").innerHTML = `
        📊 SYMBOL: ${data.symbol} <br>
        💰 PRICE: ${data.last_price} <br><br>

        ⚡ SIGNAL: <b style="color:${data.signal_color}">${data.signal}</b><br><br>

        🎯 ENTRY: ${data.entry}<br>
        🛑 SL: ${data.sl}<br>
        🥇 TP1: ${data.tp1}<br>
        🥈 TP2: ${data.tp2}
    `;
}
</script>

</body>
</html>
"""

# ──────────────────────────────────────────
# STATUS
# ──────────────────────────────────────────
@app.get("/status")
def status():
    return {"status": "RUNNING"}
