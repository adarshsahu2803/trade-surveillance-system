import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import boto3
from boto3.dynamodb.conditions import Attr
 
# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
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
    print(product_key)
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
 
 
# Simulated API call to get historical price data
def get_historical_price_data(product_key):
    # Simulate API response with more varied price data using a random walk
    dates = pd.date_range(start="2023-01-25", end="2023-01-30", freq='H')
    
    # Initialize the price series with a starting value, e.g., 1110
    prices = [1110]
    
    # Generate random variations in price
    for i in range(1, len(dates)):
        # Generate a random percentage change between -0.5% and +0.5%
        random_change = np.random.uniform(-0.005, 0.005)
        # Update the price based on the previous price and random change
        new_price = prices[-1] * (1 + random_change)
        prices.append(new_price)
    
    # Create DataFrame with the dates and the generated prices
    df = pd.DataFrame({'Date': dates, 'Price': prices})
    return df
 
 
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
 
# Streamlit layout
st.set_page_config(layout="wide")
st.title('Communications Mapping')
 
# Main section - Transaction details as table
st.subheader('Transaction Details')
alert_df = pd.DataFrame([alert_data])
st.table(alert_df)
 
# Fetch historical price data for the product key (USDKRW in this case)
price_data = get_historical_price_data(alert_data['ProductKey'])
 
 
 
# Plot price history
fig = px.line(price_data, x='Date', y='Price', title=f"{alert_data['ProductKey']} Price History")
 
# Add markers for communication and trade execution times (use random times)
comm_time = datetime(2023, 1, 27, 9, 15)
trade_time = datetime(2023, 1, 27, 9, 16)
fig.add_scatter(x=[comm_time], y=[1115], mode='markers+text', marker=dict(color='blue', size=12), name='Comm Start', text=["Comm Start"], textposition="bottom center")
fig.add_scatter(x=[trade_time], y=[1116], mode='markers+text', marker=dict(color='red', size=12), name='Trade Executed', text=["Trade Executed"], textposition="bottom center")
 
 
fig2 = px.line(price_data, x='Date', y='Price', title=f"{alert_data['ProductKey']} Price History")
 
# Add markers for communication and trade execution times (use random times)
comm_time = datetime(2023, 1, 27, 9, 15)
trade_time = datetime(2023, 1, 27, 9, 16)
fig2.add_scatter(x=[comm_time], y=[1115], mode='markers+text', marker=dict(color='blue', size=12), name='Comm Start', text=["Comm Start"], textposition="bottom center")
fig2.add_scatter(x=[trade_time], y=[1116], mode='markers+text', marker=dict(color='red', size=12), name='Trade Executed', text=["Trade Executed"], textposition="bottom center")
 
pane1, pane2 = st.columns([2,1])
 
with pane1:
    st.subheader('Price History with Timeline')
    st.plotly_chart(fig)
    st.subheader('Stats History with Trade')
    st.plotly_chart(fig2)
    # Price history graph with markers
    
 
with pane2:
    st.subheader('Conversations')
    conversationNum = 1
    for comm in comms_data:
        # print(comm['OriginalData'])
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