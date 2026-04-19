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

# ─────────────────────────────
# MOCK DATA
# ─────────────────────────────
def fetch_candles(limit=100):
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
            "low": round(low_p, 2),
            "close": round(close_p, 2),
        })

        price = close_p

    return candles

# ─────────────────────────────
# API
# ─────────────────────────────
@app.get("/analyze")
def analyze():
    candles = fetch_candles()
    last = candles[-1]["close"]

    return {
        "symbol": "XAUUSD",
        "last_price": last,
        "signal": "⏳ WAIT & SEE",
        "signal_color": "orange",
        "entry": last,
        "sl": round(last + 5, 2),
        "tp1": round(last - 5, 2),
        "tp2": round(last - 10, 2),
        "candles": candles
    }

# ─────────────────────────────
# DASHBOARD UI (AUTO LOAD)
# ─────────────────────────────
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

<h1 style="text-align:center;">🚀 INBUTPOWERFULLFX AI</h1>

<div id="chart" style="height:400px;"></div>

<div id="signal" style="text-align:center;margin-top:20px;font-size:18px;"></div>

<script>
const chart = LightweightCharts.createChart(document.getElementById('chart'), {
    layout: { background: { color: '#0f172a' }, textColor: '#DDD' },
    width: window.innerWidth,
    height: 400
});

const candleSeries = chart.addCandlestickSeries();

async function loadData() {
    try {
        const res = await fetch('/analyze');
        const data = await res.json();

        const candles = data.candles.map(c => ({
            time: c.time,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close
        }));

        candleSeries.setData(candles);

        document.getElementById("signal").innerHTML = `
            📊 SYMBOL: ${data.symbol} <br>
            💰 PRICE: ${data.last_price} <br><br>

            ⚡ SIGNAL: <b style="color:${data.signal_color}">
            ${data.signal}</b><br><br>

            🎯 ENTRY: ${data.entry}<br>
            🛑 SL: ${data.sl}<br>
            🥇 TP1: ${data.tp1}<br>
            🥈 TP2: ${data.tp2}
        `;
    } catch (err) {
        document.getElementById("signal").innerHTML =
            "❌ ERROR LOAD DATA";
    }
}

// AUTO LOAD SAAT BUKA
loadData();
</script>

</body>
</html>
"""

# ─────────────────────────────
@app.get("/status")
def status():
    return {"status": "RUNNING"}
