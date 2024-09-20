import streamlit as st
import pandas as pd
import pandas as pd

def show_communications():
    session_file_path = 'src/session_data.txt'
    try:
        df_comms = pd.read_csv(session_file_path)
    except FileNotFoundError:
        df_comms = pd.DataFrame()  # Create an empty DataFrame if the file doesn't exist

    st.dataframe(df_comms)

        
        # empty_df = pd.DataFrame(columns=columns)