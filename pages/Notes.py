import streamlit as st
import pandas as pd
import boto3
import json
import re
from scripts.assistant import get_summary

def show_notes():

    # Define columns for the layout
    col1, col2 = st.columns(2)

    # Right Column: Summary Section
    with col1:
        product_key = 'USDHKD'

        with st.spinner('Generating summary...'):
            summary = get_summary(product_key)  # Call the backend function
            st.subheader("Alert Summary")
            st.write(summary)
    
    # Left Column: Notes Section
    with col2:
        st.header("Notes")
        notes = st.text_area("Write your notes here", height=500)
