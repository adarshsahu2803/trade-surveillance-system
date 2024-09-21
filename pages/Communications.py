import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

def show_communications():
    session_file_path = 'src/session_data.txt'
    try:
        df_comms = pd.read_csv(session_file_path)
        df_fin = df_comms.drop(columns=['Selected'])
        df_fin['AlertCreationDate'] = pd.to_datetime(df_fin['AlertCreationDate']).dt.strftime('%Y-%m-%d')
        df_fin['AlertDate'] = pd.to_datetime(df_fin['AlertDate']).dt.strftime('%Y-%m-%d')
    except FileNotFoundError:
        df_fin = pd.DataFrame()  # Create an empty DataFrame if the file doesn't exist

    st.dataframe(df_fin, hide_index=True)

    if not df_fin.empty:
        product_key = df_fin['ProductKey'].iloc[0] 
    else:
        product_key = None

    # Streamlit app title
    st.title("Market Insight")

    # Define currency pair to yfinance ticker map
    currency_pair_map = {
        'USDHKD': 'HKD=X',
        'USDKRW': 'KRW=X',
        'EURJPY': 'EURJPY=X'
    }

    # Get the correct yfinance ticker
    yf_ticker = currency_pair_map[product_key]

    # Input for AlertCreationDate
    alert_creation_date = df_fin['AlertCreationDate'].iloc[0]

    # Get the most recent date
    end_date = pd.Timestamp.today().date().strftime('%Y-%m-%d')

    # Download the historical data based on user inputs
    data = yf.download(yf_ticker, start=alert_creation_date, end=end_date)

    # Check if data is available
    if not data.empty:
        # Create two subplots for Price and Volume
        fig, ax = plt.subplots(2, 1, figsize=(10, 8))

        fig.subplots_adjust(hspace=0.4)  # Adjust vertical spacing between the plots

        # Plot Close Price
        ax[0].plot(data.index, data['Close'], label='Close Price', color='b')
        ax[0].set_title(f'{product_key} Price (Close) from {alert_creation_date} to {end_date}')
        ax[0].set_xlabel('Date')
        ax[0].set_ylabel('Price')
        ax[0].grid(True)
        ax[0].legend()

        # # Plot Volume as a bar chart if available
        # if 'Volume' in data.columns:
        #     ax[1].bar(data.index, data['Volume'], label='Volume', color='g')
        #     ax[1].set_title(f'{product_key} Volume from {alert_creation_date} to {end_date}')
        #     ax[1].set_xlabel('Date')
        #     ax[1].set_ylabel('Volume')
        #     ax[1].grid(True)
        #     ax[1].legend()
        # else:
        #     st.warning("Volume data is not available for this currency pair.")

        # Generate synthetic volume data
        date_range = pd.date_range(start=alert_creation_date, end=end_date, freq='B')  # Business days
        synthetic_volume = np.random.randint(1000, 10000, size=len(date_range))

        # Create a DataFrame for the synthetic volume
        volume_data = pd.DataFrame({'Volume': synthetic_volume}, index=date_range)

        # Resample volume data to weekly frequency
        weekly_volume = volume_data.resample('W').sum()

        # Plot Volume as a bar chart with weekly aggregation
        ax[1].bar(weekly_volume.index, weekly_volume['Volume'], label='Trade Volume', color='b')
        ax[1].set_title(f'{product_key} Weekly Volume from {alert_creation_date} to {end_date}')
        ax[1].set_xlabel('Week')
        ax[1].set_ylabel('Volume')
        ax[1].grid(True)
        ax[1].legend()

        # Display the plot in Streamlit
        st.pyplot(fig)
    else:
        st.error("No data available for the selected date range and currency pair.")