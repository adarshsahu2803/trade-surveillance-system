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
import json

access_key = os.getenv('ACCESS_KEY_ID')
secret_access_key = os.getenv('SECRET_ACCESS_KEY')
bedrock_client = boto3.client('bedrock-runtime',aws_access_key_id=access_key,aws_secret_access_key=secret_access_key, region_name='us-east-1')


def show_communications():

    # Initialize the DynamoDB client
    dynamodb = boto3.resource('dynamodb',aws_access_key_id=access_key,aws_secret_access_key=secret_access_key, region_name='us-east-1')
    table = dynamodb.Table('CommsData')
    
    NewsList = []
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
    
    def summarize_text_bedrock(text_to_summarize):
        prompt = f"""
        Human: Summarize the following text into a concise summary in numbered points and different lines.Give the summary, dont give any sentence before that. Ensure that the summary captures the main points and is clear and concise. Keep it 100 words.
        Text: "{text_to_summarize}"

        Summary:
        Assistant:
        """

        # Prepare the input for the Bedrock model
        input_data = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500  # Adjust max tokens as needed for your summaries
        }

        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
            body=json.dumps(input_data),
            contentType='application/json',
            accept='application/json'
        )

        # Extract the summary from the response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        summary = response_body.get('content', [{}])[0].get('text', '').strip()
        return summary


 


    pane1, pane2 = st.columns([9, 5])
    
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

                # Button to show summary and entities
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

                # Add the summary to session state for persistent tracking
            NewsList.append(comm['Summary'])

        # Summarize all the shortlisted summaries into one summary
        if len(NewsList)>0:
            combined_summaries = " ".join(NewsList)  # Combine summaries for further summarization
            print('COMBINED '+ combined_summaries)
            final_summary = summarize_text_bedrock(combined_summaries)  # Use your summarization function
            print('RESPONSE '+  final_summary)

            # Display the box with the final summarized output
            with st.container():
                st.markdown(
                    f"""
                    <div style='background-color: #D3D3D3; padding: 10px; border-radius: 10px; margin-top: 20px;'>
                        <strong>Final Summary of Shortlisted Conversations:</strong>
                        <p>{final_summary}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )