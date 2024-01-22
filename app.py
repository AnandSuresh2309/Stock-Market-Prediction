# from matplotlib.pyplot import axis
import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
from datetime import date
from prophet import Prophet
from prophet.plot import plot_plotly
import time
import data_loader

st.set_page_config(layout="wide")

today = date.today()
st.markdown("""
<style>
  .header {
    text-align: center;
    font-size: 36px;
    margin-bottom: 20px;
    color: Orange;
  }
""", unsafe_allow_html=True)

st.markdown(f"<h1 class='header'>{''' Stock Market Prediction '''}</h1>", unsafe_allow_html=True)

session_state = st.session_state
if "current_tab" not in session_state:
    session_state.current_tab = "Stocks History and Comparison"

comparison, real_time, prediction = st.tabs(["Stocks History and Comparison", "Real-Time View", "Stock_Prediction"])

stock_df = pd.read_csv("tickers.csv")
tickers = stock_df["Name"]

# Stocks History and Comparison 
with comparison:
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input('Start', datetime.date(2019, 1, 1))
    with col2:
        end = st.date_input('End', datetime.date.today())

    st.subheader("Stocks History and Comparison")
    dropdown = st.multiselect('Pick your company', tickers)

    with st.spinner('Loading...'):
        time.sleep(1)

    dict_csv = pd.read_csv('tickers.csv', header=None, index_col=0).to_dict()[1]
    symb_list = [dict_csv.get(i) for i in dropdown]

    if dropdown:
        df = data_loader.relativereturn(yf.download(symb_list, start, end))['Adj Close'].iloc[1:]
        raw_df = data_loader.relativereturn(yf.download(symb_list, start, end)).iloc[1:]
        raw_df.reset_index(inplace=True)

        closingPrice = yf.download(symb_list, start, end)['Adj Close'].iloc[1:]
        volume = yf.download(symb_list, start, end)['Volume'].iloc[1:]

        st.subheader(f'Raw Data {dropdown}')
        st.write(raw_df)

        line, area, bar = st.tabs(['Line Chart', 'Area Chart', 'Bar Chart'])

        chart_data = {
            "Relative Returns": df,
            "Closing Price": closingPrice,
            "Volume": volume
        }

        with line:
            data_loader.create_charts("line", chart_data, dropdown)
        with area:
            data_loader.create_charts("area", chart_data, dropdown)
        with bar:
            data_loader.create_charts("bar", chart_data, dropdown)
    else:
        st.write('Please select at least one company')

# Real-Time View
with real_time:
    st.subheader("Real-Time Stock Price")
    ticker_df = pd.read_csv("tickers.csv", header=None, index_col=0)
    ticker_lst = ticker_df[1].tolist()
    real_time_view, company_performance = st.tabs(["Real-Time", "Company Performance"])

    with company_performance:
        
        selected_company = st.selectbox("Select Company", tickers)
        data_his = yf.download(dict_csv.get(selected_company), start, end).iloc[1:]
        data_his.reset_index(inplace=True)

        charts = ("Candle Stick", "Line Chart")
        chart_option = st.selectbox("Chart Type", charts)

        if chart_option == "Candle Stick":
            data_loader.candle_data(data_his)
        else:
            data_loader.raw_data(data_his)

    with real_time_view:
                                                    
        tickers_per_page = 25 
        num_pages = len(ticker_lst) // tickers_per_page + 1
        page = st.selectbox("Select Page", range(1, num_pages + 1))

        start_index = (page - 1) * tickers_per_page
        end_index = min(start_index + tickers_per_page, len(ticker_lst))
        current_tickers = ticker_lst[start_index:end_index]

        with st.spinner('Loading data...'):
            data = data_loader.fetch_real_time_stock_data(current_tickers)
        
        st.subheader(f'Raw Data {today}')
        estimated_height = 35 * (data.shape[0] + 1)       
        data = data.style.map(lambda x: 'color: red' if float(x.replace('%', '')) < 0 else 'color: green', subset=['Change'])

        st.dataframe(data, column_config={'Chart': st.column_config.LineChartColumn(width="medium")},height=estimated_height, width=10000)

# Stock_prediction
with prediction:
    st.subheader("Stock_Prediction")
    b = st.selectbox('Pick your company', tickers)

    dict_csv = pd.read_csv('tickers.csv', header=None, index_col=0).to_dict()[1]
    symb_list = dict_csv.get(b)

    if b == "":
        st.write("Enter a Stock Name")
    
    else:
        data = yf.download(symb_list, start='2019-01-01', end=end)
        data.reset_index(inplace=True)

        st.subheader(f'Raw Data of {b}')
        st.dataframe(data, height=estimated_height, width=5000)
        data_loader.raw_data(data, pred_val = True)

        n_years = st.slider('Years of prediction:', 1, 5)
        period = n_years * 365

        df_train = data[['Date', 'Close']]
        df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})

        m = Prophet()
        m.fit(df_train)
        future = m.make_future_dataframe(periods=period)
        forecast = m.predict(future)

        st.subheader(f'Forecast Data of {b}')
        st.write(forecast)

        st.subheader(f'Forecast plot for {n_years} years')
        fig1 = plot_plotly(m, forecast)
        st.plotly_chart(fig1)

        st.subheader(f"Forecast components of {b}")
        fig2 = m.plot_components(forecast)
        st.write(fig2)