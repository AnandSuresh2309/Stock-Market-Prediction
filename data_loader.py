# Import necessary libraries
import yfinance as yf
import pandas as pd
import streamlit as st
import numpy as np
from plotly import graph_objs as go
from concurrent.futures import ThreadPoolExecutor, as_completed

# Function to calculate relative returns
def relativereturn(df):
    rel = df.pct_change()
    cumret = np.expm1(np.log1p(rel).cumsum())
    cumret = cumret.fillna(0)
    return cumret

# Function to fetch stock data for a given ticker
def fetch_stock_data(ticker):
    try:
        # Use yfinance to get historical and current stock data
        data = yf.Ticker(ticker).history(period='1d')
        data1 = yf.Ticker(ticker).history()
        historical = data1['Close']
        # Check if the data is not empty
        if not data.empty:
            # Calculate the change percentage
            data['history'] = historical
            change = (data["Close"].iloc[-1] - data["Open"].iloc[-1]) / (data["Open"].iloc[-1]) * 100
            data['Change'] = f"{change:.2%}"
            # Return a dictionary containing relevant stock information
            return {'Ticker': ticker, 'Open': data['Open'].iloc[-1], 'High': data['High'].iloc[-1], 'Low': data['Low'].iloc[-1],
                    'Close': data['Close'].iloc[-1], 'Change': data['Change'].iloc[-1], 'Volume': data['Volume'].iloc[-1], 'Chart': historical.values}
        else:
            return None
    except Exception as e:
        return None

# Function to fetch real-time stock data for a list of tickers using ThreadPoolExecutor
def fetch_real_time_stock_data(tickers):
    data_list = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_stock_data, ticker): ticker for ticker in tickers}

        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                data_list.append(result)

    # Create a DataFrame from the collected data
    df = pd.DataFrame(data_list)
    return df

# Function to create a Candlestick Chart using Plotly
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
    # Update layout for aesthetics
    fig.update_layout(
        title="Candlestick Chart",
        yaxis_title="Stock Price",
        xaxis_title="Date",
        plot_bgcolor="black",
        paper_bgcolor="black",
        font_color="white",
    )
    # Display the Candlestick Chart using Streamlit
    st.plotly_chart(fig)

# Function to create a Line Chart using Plotly
def raw_data(data, pred_val= None):
    fig = go.Figure(data=[
        go.Scatter(x=data['Date'], y=data['Open'], name="stock_open", line=dict(color="royalblue")),
        go.Scatter(x=data['Date'], y=data['Close'], name="stock_close", line=dict(color="orange"))
    ])
    # Update layout for aesthetics
    if pred_val:
        fig.layout.update(title_text=f'Time Series Data', xaxis_rangeslider_visible=True)
    else:
        fig.layout.update(title_text='Line Chart', xaxis_rangeslider_visible=True)
    # Display the Line Chart using Streamlit
    st.plotly_chart(fig)

# Function to create various types of charts based on user input
def create_charts(chart_type, chart_data, dropdown):
    for title, data in chart_data.items():
        st.write(f"### {title} of {dropdown}")
        # Use getattr to dynamically call the appropriate Streamlit chart function
        getattr(st, f"{chart_type}_chart")(data)