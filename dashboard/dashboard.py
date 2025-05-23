import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

st.title("Crypto Trading Dashboard")

symbol = st.text_input("Enter Symbol (e.g., BTC-USD)", "BTC-USD")
df = yf.download(symbol, period="3mo", interval="1d")

df['MA20'] = df['Close'].rolling(window=20).mean()
df['MA50'] = df['Close'].rolling(window=50).mean()

fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close'))
fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20'))
fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], name='MA50'))

st.plotly_chart(fig)
