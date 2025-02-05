import streamlit as st
import sys
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import logging
import subprocess
import crud

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime

# Configure logging
logging.basicConfig(filename="error_log.txt", level=logging.ERROR, format="%(asctime)s - %(message)s")

# Set pate go wide 
st.set_page_config(layout="wide")

# Streamlit App Title
st.title("📈 Stock Market and News Sentiment Analysis")

col1, col2, col3, col4 = st.columns(4)

with col1:
    # User Input for Ticker Symbols
    tickers = st.text_input("Enter Stock Tickers (comma-separated):", "MSFT")

with col2:
    # Date Range Selection
    start_date = st.date_input("Start Date", pd.to_datetime("2024-01-01"))

with col3:
    end_date = st.date_input("End Date", pd.to_datetime("today"))

with col4:
    # Interval Selection Dropdown
    interval_options = ["1m", "2m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo", "3mo"]
    selected_interval = st.selectbox("Select Time Interval", interval_options, index=6)  # Default: "1d"


# Toggle for Bollinger Bands & SMA
show_bb = st.toggle("Show Bollinger Bands", value=False)
show_sma = st.toggle("Show Simple Moving Average (SMA)", value=False)

# Function to Fetch Stock Data with Error Handling
@st.cache_data
def get_stock_data(ticker, start, end, interval):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(start=start, end=end, interval=interval)

        if data.empty:
            raise ValueError(f"{ticker}: No data found for selected interval ({interval}). Yahoo Finance restriction.")

        return data
    except Exception as e:
        error_message = f"⚠️ Error fetching {ticker} data: {str(e)}"
        logging.error(error_message)
        return None  # Return None if there's an error

# Function to Calculate Bollinger Bands
def calculate_bollinger_bands(data, period=20):
    data["BB_Middle"] = data["Close"].rolling(window=period).mean()
    data["BB_Upper"] = data["BB_Middle"] + (data["Close"].rolling(window=period).std() * 2)
    data["BB_Lower"] = data["BB_Middle"] - (data["Close"].rolling(window=period).std() * 2)
    return data

# Function to Calculate SMA with Validation
def calculate_sma(data, period):
    if period > 0 and period <= len(data):
        data[f"SMA_{period}"] = data["Close"].rolling(window=period).mean()
    else:
        data[f"SMA_{period}"] = np.nan  # Invalid period, set to NaN
    return data

# Process multiple tickers
ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]

if ticker_list:
    for ticker in ticker_list:
        company_data = yf.Ticker(ticker)
        company_name = company_data.info['longName']
        st.subheader(f"📊 {company_name} - {selected_interval} Interval Data")

        data = get_stock_data(ticker, start_date, end_date, selected_interval)

        if data is None:
            st.error(f"⚠️ Error: No data available for {ticker} at {selected_interval} interval. Check the date range.")
        else:
            # Validate SMA Period Input only if SMA toggle is enabled
            if show_sma:
                max_period = len(data)
                sma_period = st.number_input(
                    f"Enter SMA Period for {ticker}:",
                    min_value=1,
                    max_value=max_period,
                    value=min(20, max_period),  # Default to 20 or max available data
                    step=1
                )
            else:
                sma_period = None  # If SMA is disabled, no period is needed

            # Calculate Indicators if enabled
            if show_bb:
                data = calculate_bollinger_bands(data)
            if show_sma and sma_period:
                data = calculate_sma(data, sma_period)

            with st.expander(f"📋 Show Data for {ticker}"):
                st.write(data)

            if st.button(f"💾 Persist Data for {ticker}"):
                if not data.empty:
                    crud.save_stock_data_to_db(ticker, data)
                    st.success(f"✅ Stock price data for {ticker} has been saved to the database!")
                else:
                    st.warning(f"⚠️ No data available for {ticker} to save.")

            if st.button(f"🗑️ Delete {ticker} Data"):
                if not data.empty:
                    crud.delete_stock_data(ticker)
                    st.success(f"✅ Stock price data for {ticker} has been deleted from the database!")
                else:
                    st.warning(f"⚠️ No data available for {ticker} to save.")
            

            # Candlestick Chart (No Range Slider)
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name="Candlestick"
            ))

            # Add Bollinger Bands if enabled
            if show_bb:
                fig.add_trace(go.Scatter(
                    x=data.index, y=data["BB_Upper"], mode="lines", name="Upper Bollinger Band", line=dict(color='rgb(20, 10, 130)')
                ))
                fig.add_trace(go.Scatter(
                    x=data.index, y=data["BB_Lower"], mode="lines", name="Lower Bollinger Band", line=dict(color='rgb(20, 10, 130)')
                ))

            # Add SMA if enabled
            if show_sma and sma_period:
                fig.add_trace(go.Scatter(
                    x=data.index, y=data[f"SMA_{sma_period}"], mode="lines", name=f"SMA ({sma_period})", line=dict(color='blue')
                ))

            fig.update_layout(
                title=f"{company_name} | Candlestick Chart ({selected_interval} interval)",
                xaxis_title="Date",
                yaxis_title="Price",
                xaxis_rangeslider_visible=False  # Remove lower slicer
            )

            st.plotly_chart(fig)


st.markdown('''------''')

# Section for Scraping Yahoo Finance News
st.subheader("📢 Latest News & Sentiment Analysis")

# User input for ticker to scrape news
scrape_ticker = st.text_input("Enter Ticker Symbol for News Scraping:")

# Separate button to scrape news without refreshing the whole app
if st.button("📰 Scrape News"):
    if scrape_ticker:
        with st.spinner(f"Scraping news for {scrape_ticker} ..."):
            result = subprocess.run(["python", "newsData.py", scrape_ticker], capture_output=True, text=True)
            if result.returncode == 0:
                st.success(f"✅ Successfully scraped news for {scrape_ticker}!")

                # sentiment analysis
                # subprocess.run(["python", "sentimentAnalysis.py", "news_articles_by_ticker.csv"], check=True)
                subprocess.run([sys.executable, "sentimentAnalysis.py", "news_articles_by_ticker.csv"], check=True)
            else:
                st.error(f"⚠️ Error occurred: {result.stderr}")
    else:
        st.error("⚠️ Please enter a valid ticker symbol.")


try:
    # Add table
    file_name = "news_articles_by_ticker.csv"
    ticker_news = pd.read_csv(file_name)
    columns_to_drop = ["Affected Tickers"]
    ticker_news = ticker_news.drop(columns_to_drop, axis=1)


    # Column-wise search filters in a single row
    st.subheader("🔍 Filter News by Column")
    filter_cols_ticker = st.columns(4)  # Create 4 columns for search boxes

    search_filters_ticker = {}
    column_names_ticker = ["Sentiment", "Title", "Short Description", "Source"]

    # Create aligned search input boxes
    for i, col_name in enumerate(column_names_ticker):
        with filter_cols_ticker[i]:  # Place each search box in the corresponding column
            search_filters_ticker[col_name] = st.text_input(f"Filter by {col_name}", "").strip()

    # Apply search filters dynamically
    for col, search_text in search_filters_ticker.items():
        if search_text:
            ticker_news = ticker_news[ticker_news[col].astype(str).str.contains(search_text, case=False, na=False)]

    st.subheader(f"📰 News & Sentiment Analysis")
    st.dataframe(ticker_news, width=2000, height=600)  # Customize width & height

except FileNotFoundError:
    pass
    # st.warning(f"⚠️ {ticker_news} not found. Select a ticker to download the news for.")

news_file = "news_articles_by_ticker.csv"

try:
    # Load data
    df = pd.read_csv(news_file)

    # Ensure the Sentiment column exists
    if "Sentiment" not in df.columns:
        st.error("❌ 'Sentiment' column not found in dataset!")
    else:
        # Count occurrences of each sentiment category
        sentiment_counts = df["Sentiment"].value_counts()

        # Define sentiment weights
        sentiment_weights = np.array([1, 0, -1])  # Bullish = 1, Neutral = 0, Bearish = -1
        sentiment_values = np.array([
            sentiment_counts.get("Bullish", 0),
            sentiment_counts.get("Neutral", 0),
            sentiment_counts.get("Bearish", 0)
        ])

        # Compute the combined sentiment score using a dot product
        combined_score = np.dot(sentiment_values, sentiment_weights)

        # Create a DataFrame for visualization
        sentiment_data = pd.DataFrame({
            "Sentiment": ["Bullish", "Neutral", "Bearish", "Combined Score"],
            "Count": np.append(sentiment_values, combined_score)  # Append combined score as fourth bar
        })

        st.markdown('''------''')

        # Streamlit App Title
        st.subheader("📊 Sentiment Cluster Analysis")

        if st.button("💾 Persist Sentiment Data"):
            for _, row in sentiment_data.iterrows():
                crud.save_sentiment_to_db(scrape_ticker, row["Sentiment"], row["Count"])
            st.success("Data successfully saved to db.")

        # Generate the Bar Chart
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.bar(sentiment_data["Sentiment"], sentiment_data["Count"], color=["green", "gray", "red", "blue"])
        ax.set_xlabel("Sentiment Category")
        ax.set_ylabel("Score")
        ax.set_title("Sentiment Distribution and Combined Score")

        # Display Bar Chart
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.pyplot(fig)

except FileNotFoundError:
    pass


st.markdown('''------''')


st.subheader("📊 Stored Stock Data")

if st.button("🛢Load Data from DB"):
    stored_data = crud.get_stock_data_from_db()
    st.dataframe(stored_data)

if st.button("🗑️ Delete Data from DB"):
    crud.truncate_stock_data()
    st.success("All data was successfully deleted.")
    

st.markdown('''------''')


st.subheader("📊 Stored Sentiment Analysis")
if st.button("🛢 Load Sentiment Data"):
    sentiment_data = crud.get_sentiment_data_from_db()

    with st.spinner("Fetching sentiment data... ⏳"):
        sentiment_df = crud.get_sentiment_data_from_db()

        if sentiment_df.empty:
            st.warning("⚠️ No sentiment data available.")
        else:
            st.success("✅ Sentiment data loaded successfully!")

            # Aggregate data by ticker (sum sentiment scores per ticker)
            sentiment_agg = sentiment_df[sentiment_df["sentiment"] == "Combined Score"]  # sentiment_df.groupby("ticker")["sentiment_score"].sum().reset_index()
            sentiment_agg = sentiment_agg.groupby("ticker")["sentiment_score"].mean().reset_index()

            # Plot bar chart
            fig, ax = plt.subplots(figsize=(10, 5))
            bars = ax.bar(sentiment_agg["ticker"], sentiment_agg["sentiment_score"], color="royalblue")

            # Add data labels on top of bars
            for bar in bars:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

            ax.set_xlabel("Ticker", fontsize=12)
            ax.set_ylabel("Combined Sentiment Score", fontsize=12)
            ax.set_title("Sentiment Score by Ticker", fontsize=14)
            ax.grid(axis="y", linestyle="--", alpha=0.7)

            # Display chart in Streamlit
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.pyplot(fig)


if st.button("🧹 Clean Sentiment DB"):
    crud.clean_sentiment_data()
    st.success("Records with missing data were deleted.")

if st.button("🗑️ Delete Sentiment Data"):
    crud.delete_sentiment_data()
    st.success("All data was successfully deleted.")


st.markdown('''------''')

# Show Error Log Button
if st.button("Show Error Log"):
    try:
        with open("error_log.txt", "r") as file:
            st.text(file.read())
    except FileNotFoundError:
        st.warning("No errors logged yet.")
