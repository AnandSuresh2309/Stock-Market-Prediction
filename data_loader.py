import yfinance as yf
import pandas as pd
import streamlit as st
import numpy as np
from plotly import graph_objs as go
from concurrent.futures import ThreadPoolExecutor, as_completed


def relativereturn(df):
    rel = df.pct_change()
    cumret = np.expm1(np.log1p(rel).cumsum())
    cumret = cumret.fillna(0)
    return cumret

def fetch_stock_data(ticker):
    try:
        data = yf.Ticker(ticker).history(period='1d')
        data1 = yf.Ticker(ticker).history()
        historical = data1['Close']
        if not data.empty:
            data['history'] = historical
            change = (data["Close"].iloc[-1] - data["Open"].iloc[-1]) / (data["Open"].iloc[-1]) * 100
            data['Change'] = f"{change:.2%}"
            return {'Ticker': ticker, 'Open': data['Open'].iloc[-1], 'High': data['High'].iloc[-1], 'Low': data['Low'].iloc[-1],
                    'Close': data['Close'].iloc[-1], 'Change': data['Change'].iloc[-1], 'Volume': data['Volume'].iloc[-1], 'Chart': historical.values}
        else:
            return None
    except Exception as e:
        return None

# @st.cache_data(ttl=3600, show_spinner=False)
def fetch_real_time_stock_data(tickers):
    data_list = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_stock_data, ticker): ticker for ticker in tickers}

        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                data_list.append(result)

    df = pd.DataFrame(data_list)
    return df

def candle_data(data):
    fig = go.Figure(data=[go.Candlestick(
        x=data["Date"],
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        increasing_line_color="#F70D1A",  
        decreasing_line_color="#089000",
    )])
    fig.update_layout(
        title="Candlestick Chart",
        yaxis_title="Stock Price",
        xaxis_title="Date",
        plot_bgcolor="black",
        paper_bgcolor="black",
        font_color="white",
    )
    st.plotly_chart(fig)

def raw_data(data, pred_val= None):
    fig = go.Figure(data=[
        go.Scatter(x=data['Date'], y=data['Open'], name="stock_open", line=dict(color="royalblue")),
        go.Scatter(x=data['Date'], y=data['Close'], name="stock_close", line=dict(color="orange"))
    ])
    if pred_val:
        fig.layout.update(title_text=f'Time Series Data', xaxis_rangeslider_visible=True)
    else:
        fig.layout.update(title_text='Line Chart', xaxis_rangeslider_visible=True)
    st.plotly_chart(fig)

def create_charts(chart_type, chart_data, dropdown):
    for title, data in chart_data.items():
        st.write(f"### {title} of {dropdown}")
        getattr(st, f"{chart_type}_chart")(data)