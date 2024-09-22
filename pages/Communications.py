import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import boto3
from boto3.dynamodb.conditions import Attr
import os
from dotenv import load_dotenv
import yfinance as yf
import matplotlib.pyplot as plt

access_key = os.getenv('ACCESS_KEY_ID')
secret_access_key = os.getenv('SECRET_ACCESS_KEY')

def show_communications():

    # Initialize the DynamoDB client
    dynamodb = boto3.resource('dynamodb',aws_access_key_id=access_key,aws_secret_access_key=secret_access_key, region_name='us-east-1')
    table = dynamodb.Table('CommsData')
    

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
        email = df_fin['Trader'].iloc[0] 
    else:
        product_key = None
        email = None

    def query_comms(email, product_key):
        """
        Query the DynamoDB table to retrieve communications that contain either a specific email or product key.
        
        Parameters:
        - email (str): The email to search for.
        - product_key (str): The product key to search for (e.g., "EURJPY").
        
        Returns:
        - List of communications (dictionaries) that contain either the email or the product key.
        """
        if len(product_key) == 6:
            product_key = product_key[:3] + '/' + product_key[3:]
        # Use | (bitwise OR) to combine the conditions
        filter_expression = Attr('Entities').contains(email) | Attr('Entities').contains(product_key)
        
        # Scan the table with the filter expression
        response = table.scan(
            FilterExpression=filter_expression
        )
    
        communications = response.get('Items', [])
        
        # Handle pagination if there are more results
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=filter_expression,
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            communications.extend(response.get('Items', []))
    
        return communications
    
    comms_data = query_comms(product_key=product_key, email=email)
    
    def format_conversation(original_data):
        """
        Format the conversation so that the speaker's name, role, and email are bold, followed by the conversation text.
        """
        formatted_conversation = ""
        
        # Split the conversation by lines (assuming each line is a separate message)
        conversation_lines = original_data.split("\n")
    
        restructured_lines = []
        combined_line = ""
    
        for line in conversation_lines:
            # Check if the line starts with a number followed by a comma
            if line.strip() and line.split(", ")[0].isdigit():
                # If it's a new numbered line, append the previous combined_line (if any) and start a new one
                if combined_line:
                    restructured_lines.append(combined_line.strip())
                combined_line = line  # Start a new line
            else:
                # If it's a continuation, append to the current combined_line
                combined_line += " " + line.strip()
    
        # Append the last line
        if combined_line:
            restructured_lines.append(combined_line.strip())
    
        flag = -1
        prev_email = ''
    
        for line in restructured_lines:
            
            parts = line.split(", ")
            if len(parts) >= 5:
                company = parts[1]  # Name of the speaker
                email = parts[3]  # Role (e.g., Client, Salesperson)
                time = parts[2]  # Email of the speaker
                message = ", ".join(parts[4:-1])  # The actual message
                role = parts[-1]
                # Format the speaker's info in bold and the message in regular text
    
                if prev_email != email:
                    flag = flag * -1
    
                if flag == -1:
                    formatted_conversation += f'<strong><span style="color:CornflowerBlue">{email}, {role}, {company}, {time}</span></strong>: {message}<br><hr style="border: 0.5px solid lightgrey; margin: 5px 0;">'
                else:
                    formatted_conversation += f'<strong><span style="color:Tomato">{email}, {role}, {company}, {time}</span></strong>: {message}<br><hr style="border: 0.5px solid lightgrey; margin: 5px 0;">'
                
                prev_email = email
        return formatted_conversation
 

    pane1, empty_pane, pane2 = st.columns([9, 0.5, 5])
    
    with pane1:

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
    
    with pane2:
        st.subheader('Communications')
        conversationNum = 1
        for comm in comms_data:
            with st.expander(f"View Conversation {conversationNum}"):
                conversationNum += 1
                # Display the original data
                formatted_chat = format_conversation(comm['OriginalData'])
                st.markdown(
                    f"""
                    <div style='background-color: #f0f0f0; padding: 10px; border-radius: 10px; margin-bottom: 10px;'>
                        <strong>Original Data:</strong>
                        <p>{formatted_chat}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Streamlit button styled as a part of the card (you can use CSS to style it further)
                if st.button(f"Summarize ID:{comm['CommID']}"):
                    # Show summary and entities when the button is clicked
                    st.markdown(
                        f"""
                        <div style='background-color: #ffffff; padding: 10px; border-radius: 10px; margin-bottom: 10px;'>
                            <strong>Summary:</strong>
                            <p>{comm['Summary']}</p>
                            <strong>Entities:</strong>
                            <div style='display: flex; flex-wrap: wrap;'>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Handle entity display as inline blocks
                    entities = comm['Entities']
                    entity_tags = ""
                    for entity in entities:
                        entity_tags += f"<span style='background-color: #ffcccc; border-radius: 5px; padding: 5px; margin: 3px; display: inline-block;'>{entity}</span>"
                    
                    st.markdown(f"<div style='display: flex; flex-wrap: wrap;'>{entity_tags}</div>", unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)