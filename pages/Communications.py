import streamlit as st
import pandas as pd

def show_communications():
    session_file_path = 'src/session_data.txt'
    try:
        df_comms = pd.read_csv(session_file_path)
        df_fin = df_comms.drop(columns=['Selected'])
    except FileNotFoundError:
        df_fin = pd.DataFrame()  # Create an empty DataFrame if the file doesn't exist

    st.dataframe(df_fin)

    if not df_fin.empty:
        product_key = df_fin['ProductKey'].iloc[0] 
    else:
        product_key = None
