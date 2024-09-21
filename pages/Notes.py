import streamlit as st
import pandas as pd
import boto3
import json
import re
from scripts.assistant import get_summary

def show_notes():

    session_file_path = 'src/session_data.txt'
    try:
        df = pd.read_csv(session_file_path)
        df_fin = df.drop(columns=['Selected'])
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

        with st.spinner('Generating summary...'):
            summary = get_summary(product_key)  # Call the backend function
            st.subheader("Alert Summary")
            st.write(summary)
    
    # Left Column: Notes Section
    with col2:
        st.header("Notes")
        notes = st.text_area("Write your notes here", height=500)
        st.download_button("Save", data = notes, file_name ="MyNotes.txt" )
