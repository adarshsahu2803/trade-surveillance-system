# import streamlit as st

# def show_notes():
#     st.title("Notes")
#     st.write("This is Notes window.")


import streamlit as st
import pandas as pd
import boto3
import json
import re
from scripts.assistant import get_summary

def show_notes():

    # Streamlit UI layout
    # def main():
    st.title("Product Summary and Notes")

    # Define columns for the layout
    col1, col2 = st.columns(2)

    # Left Column: Notes Section
    with col1:
        st.header("Notes")
        notes = st.text_area("Write your notes here", height=300)

    # Right Column: Summary Section
    with col2:
        st.header("Product Summary")

        # Input field for product key
        product_key = st.text_input("Enter the product key:", "")

        if st.button("Get Summary"):
            if product_key:
                with st.spinner('Generating summary...'):
                    summary = get_summary(product_key)  # Call the backend function
                    st.subheader("Summary Output")
                    st.write(summary)
            else:
                st.error("Please enter a product key.")
