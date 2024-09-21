import streamlit as st
import requests
from scripts.assistant import execute_sql_query, connect_to_rds
# from src.agstyler import draw_grid
from st_aggrid import GridOptionsBuilder, GridUpdateMode, AgGrid
import json
import os
import pandas as pd

def show_alerts():

    backend_url = 'http://172.31.18.21:5000/query'
    # Split the window into two columns
    left_col, empty_col, right_col = st.columns([9, 0.5, 5])

    # Upper half of the left column: 5 tabs for different alert types
    with left_col:
        st.subheader("Critical Alerts")

        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Front Running", "Spoofing", "Insider Trading", "Layering", "Ramping"])

        # Data placeholder
        df = None

        session_file_path = 'src/session_data.txt'

        # Logic for loading datasets when tabs are clicked
        with tab1:
            # SQL query to retrieve data from the 'front_running' table
                query = "SELECT * FROM front_running"
            
            # Establish RDS connection and execute the query
                conn = connect_to_rds()
                df = execute_sql_query(query, conn)
                
                if 'Selected' not in df.columns:
                    df.insert(0, 'Selected', None)

                # Use AgGrid to display the DataFrame
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_selection(selection_mode='single', use_checkbox=True)  # Enable checkboxes for selection
                grid_options = gb.build()

                # Display the grid with the configured options
                grid_response = AgGrid(
                    df,
                    gridOptions=grid_options,
                    update_mode=GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.VALUE_CHANGED,
                    height=400,
                    allow_unsafe_jscode=True,  # Required for custom JavaScript in AgGrid
                    key='critical_alerts_grid',
                    enable_enterprise_modules=False
                )

                # Update the session state with the selected rows
                selected_rows = grid_response['selected_rows']

                # Call the update function to modify the session_data.txt file
                update_session_data(selected_rows)

        with tab2:
            query = "SELECT * FROM spoofing"
            
            # Establish RDS connection and execute the query
            conn = connect_to_rds()
            try:
                df = execute_sql_query(query, conn)
                st.dataframe(df)
            except Exception as e:
                st.error(f"Error querying the database: {e}")
            finally:
                conn.close()  # Ensure the connection is closed

        with tab3:
            query = "SELECT * FROM insider_trading"
            
            # Establish RDS connection and execute the query
            conn = connect_to_rds()
            try:
                df = execute_sql_query(query, conn)
                st.dataframe(df)
            except Exception as e:
                st.error(f"Error querying the database: {e}")
            finally:
                conn.close()  # Ensure the connection is closed

        with tab4:
            query = "SELECT * FROM layering"
            
            # Establish RDS connection and execute the query
            conn = connect_to_rds()
            try:
                df = execute_sql_query(query, conn)
                st.dataframe(df)
            except Exception as e:
                st.error(f"Error querying the database: {e}")
            finally:
                conn.close()  # Ensure the connection is closed

        with tab5:
            query = "SELECT * FROM ramping"
            
            # Establish RDS connection and execute the query
            conn = connect_to_rds()
            try:
                df = execute_sql_query(query, conn)
                st.dataframe(df)
            except Exception as e:
                st.error(f"Error querying the database: {e}")
            finally:
                conn.close()  # Ensure the connection is closed

    # Define custom CSS to hide the GitHub icon and adjust the text area
    custom_css = """
    <style>
    .st-emotion-cache-30do4w  {
        visibility: hidden;
    }
    .e3g6aar1 {
        visibility: hidden;
    }
    .st-emotion-cache-1wbqy5l {
        visibility: hidden;
    }
    .stTextArea {
        margin-top: -25px; /* Adjust the value to move the text area up */
    }
    </style>
    """

    # Inject custom CSS
    st.markdown(custom_css, unsafe_allow_html=True)

    # Right half: Chatbot
    with right_col:
        st.header("Trade Surveillance Assistant")
        user_query = st.text_input("Ask a question:")
        if st.button("Submit"):
            response = requests.post(backend_url, json={"query": user_query})
            if response.status_code == 200:
               data = response.json()
               #st.write(data)  # Log the entire response for debugging
               st.text_area("", data.get('combined_response', ''), height=250)
            else:
               st.error("Failed to get response from the chatbot")


def update_session_data(selected_rows):
    session_file_path = 'src/session_data.txt'

    if not selected_rows is None:
        selected_rows.to_csv(session_file_path, index=True)

# Function to check if the CSV file has a DataFrame and get the index
def get_index_from_csv(file_path):
    try:
        df = pd.read_csv(file_path, index_col=0)  # Use the first column as index
        if not df.empty:
            return df.index[0]  # Return the first index value
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return None  # Return None if file doesn't exist or is empty
    return None
