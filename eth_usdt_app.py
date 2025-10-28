import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time
from datetime import datetime
from twilio.rest import Client
import os

# ---- Twilio Config (Environment Variables) ----
ACCOUNT_SID = os.getenv("TWILIO_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
WHATSAPP_FROM = "whatsapp:+14155238886"       # Twilio sandbox number
WHATSAPP_TO = "whatsapp:+918309641852"        # Your number with country code

# ---- Streamlit Layout ----
st.set_page_config(page_title="ETH/USDT Realtime Chart", layout="wide")
st.title("🚀 ETH/USDT Realtime Candlestick Chart (CoinDCX REST API)")
st.caption("Realtime refresh every 1s + WhatsApp alerts via Twilio")

low = st.number_input("Enter Lower Price Limit (USDT):", value=2500.0)
high = st.number_input("Enter Upper Price Limit (USDT):", value=2800.0)

price_display = st.empty()
chart = st.empty()
alert_box = st.empty()

# ---- DataFrame for Candles ----
data = pd.DataFrame(columns=["time", "open", "high", "low", "close"])

# ---- WhatsApp Alert ----
def send_whatsapp_alert(price):
    try:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        msg = f"🚨 ETH/USDT Alert: Current Price = {price:.2f} USDT (within {low}-{high})"
        client.messages.create(
            from_=WHATSAPP_FROM,
            to=WHATSAPP_TO,
            body=msg
        )
        alert_box.success(f"✅ WhatsApp alert sent: {msg}")
    except Exception as e:
        alert_box.error(f"❌ WhatsApp alert failed: {e}")

# ---- Function to get price from CoinDCX ----
def get_eth_price():
    try:
        r = requests.get("https://api.coindcx.com/exchange/ticker", timeout=10)
        all_data = r.json()
        for coin in all_data:
            if coin["market"] == "ETHUSDT":
                return float(coin["last_price"])
    except Exception:
        return None

# ---- Live Loop ----
st.info("📡 Fetching ETH/USDT live prices from CoinDCX…")

while True:
    price = get_eth_price()
    if price:
        now = datetime.now()
        price_display.markdown(f"### 💰 Current ETH/USDT: **${price:.2f}**")

        # Add or update candle
        if data.empty or (now - data.iloc[-1]["time"]).seconds >= 60:
            data = pd.concat([data, pd.DataFrame([{
                "time": now, "open": price, "high": price,
                "low": price, "close": price
            }])])
        else:
            data.iloc[-1, data.columns.get_loc("high")] = max(data.iloc[-1]["high"], price)
            data.iloc[-1, data.columns.get_loc("low")] = min(data.iloc[-1]["low"], price)
            data.iloc[-1, data.columns.get_loc("close")] = price

        # Keep recent 100 candles
        if len(data) > 100:
            data = data.iloc[-100:]

        # Plot Candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=data["time"],
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            increasing_line_color="green",
            decreasing_line_color="red"
        )])
        fig.update_layout(height=500, xaxis_rangeslider_visible=False)
        chart.plotly_chart(fig, use_container_width=True, key=str(time.time()))

        # Alert check
        if low <= price <= high:
            send_whatsapp_alert(price)

    time.sleep(1)
