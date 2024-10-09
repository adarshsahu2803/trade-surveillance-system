import streamlit as st
import pandas as pd
import boto3
import json
import re
import plotly.express as px
import numpy as np
import yfinance as yf
from scripts.assistant import get_summary

def show_notes():

    session_file_path = 'src/session_data.txt'
    try:
        df = pd.read_csv(session_file_path)
        df_fin = df.drop(columns=['Selected'])
        df_fin['AlertCreationDate'] = pd.to_datetime(df_fin['AlertCreationDate']).dt.strftime('%Y-%m-%d')
        df_fin['AlertDate'] = pd.to_datetime(df_fin['AlertDate']).dt.strftime('%Y-%m-%d')
    except FileNotFoundError:
        df_fin = pd.DataFrame()  # Create an empty DataFrame if the file doesn't exist

    st.dataframe(df_fin, hide_index=True)

    if not df_fin.empty:
        product_key = df_fin['ProductKey'].iloc[0] 
    else:
        product_key = None

    # Define columns for the layout
    col1, col2 = st.columns(2)

    # Right Column: Summary Section
    with col1:

        # Streamlit app title
        st.subheader("Market Insight")

        # Define currency pair to yfinance ticker map
        currency_pair_map = {
            'USDHKD': 'HKD=X',
            'USDKRW': 'KRW=X',
            'EURJPY': 'EURJPY=X'
        }

        # Get the correct yfinance ticker
        yf_ticker = currency_pair_map[product_key]
        # alert_creation_date = df_fin['AlertDate'].iloc[0]
        # end_date = df_fin['AlertCreationDate'].iloc[0]
        alert_creation_date = "2024-09-11"
        end_date = "2024-09-12"

        # Download hourly data
        data = yf.download(yf_ticker, start=alert_creation_date, end=end_date, interval='1h')

        # Check if data is not empty
        if not data.empty:
            np.random.seed(42)  # For reproducibility
            hourly_volume = np.random.randint(1000, 10000, size=len(data))
           
            # Add the synthetic volume to the data
            data['Volume'] = hourly_volume

            # Plot Close Price
            fig1 = px.line(data, x=data.index, y='Close', title=f'{product_key} Hourly Price (Close)',
                        labels={'Close': 'Price', 'index': 'Hour'})
           
            fig1.update_layout(xaxis_title='Time', yaxis_title='Price', template='plotly_dark',
                            title_x=0.25, margin=dict(t=80, l=40, r=40, b=40))
           
            # Plot Volume
            fig2 = px.bar(data, x=data.index, y='Volume', title=f'{product_key} Hourly Trade Volume',
                        labels={'Volume': 'Volume', 'index': 'Hour'})
            fig2.update_layout(xaxis_title='Time', yaxis_title='Volume', template='plotly_dark',
                            title_x=0.25, margin=dict(t=80, l=40, r=40, b=40))

            # Display the Price & volume plot
            st.plotly_chart(fig1)
            st.plotly_chart(fig2)
        else:
            st.write("No yfinance data")
    
    # Left Column: Notes Section
    with col2:
        with st.spinner('Generating summary...'):
            summary = get_summary(product_key)  # Call the backend function
            st.subheader("Alert Summary")
            st.write(summary)

        st.header("Notes")
        notes = st.text_area("Write your notes here", height=250)
        st.download_button("Save", data = notes, file_name ="MyNotes.txt" )
