import streamlit as st
import pandas as pd
import json
import boto3
import requests
from datetime import datetime
import plotly.express as px  
from dotenv import load_dotenv
import os
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

access_key = os.getenv('ACCESS_KEY_ID')
secret_access_key = os.getenv('SECRET_ACCESS_KEY')
 
def show_news():

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
        product_key = product_key[:3] + '/' + product_key[3:]
        TRADE_ENTRY = product_key
    else:
        TRADE_ENTRY = "stocks OR markets OR finance OR trading"

    # Hardcoded trade entry and date range
    HARD_CODED_FROM_DATE = "2024-09-09"
    HARD_CODED_TO_DATE = "2024-08-05"

    # Initialize the Bedrock runtime client
    bedrock_runtime = boto3.client(service_name='bedrock-runtime', aws_access_key_id=access_key,aws_secret_access_key=secret_access_key, region_name='us-east-1')
   

    #Convert currency pair to natural language
    def convert_currency_pair_for_api(currency_pair):
    # Dictionary to map currency codes to full names without spaces
        currency_map = {
            'EUR': 'Euro%20Trade',
            'JPY': 'Yen',
            'USD': 'US%20Dollar',
            'GBP': 'British%20Pound',
            'KRW': 'South%20Korean%20Won',
            'HKD': 'Hong%20Kong%20Dollar',
            'AUD': 'Australian%20Dollar',
            'CAD': 'Canadian%20Dollar',
            'CHF': 'Swiss%20Franc',
            'NZD': 'New%20Zealand%20Dollar',
            'CNY': 'Yuan',
            'INR': 'Rupee',
            # Add more currency codes as needed
        }
       
        # Extract the two currency codes
        first_currency = currency_pair[:3]
        second_currency = currency_pair[3:]
       
        # Convert codes to full names without spaces using the dictionary
        first_currency_full = currency_map.get(first_currency, first_currency)
        second_currency_full = currency_map.get(second_currency, second_currency)
       
        return first_currency_full, second_currency_full
    # Function to fetch articles
    def get_trade_articles(trade_entry, from_date, to_date):
        query_params = {
            "apiKey": "44539cbfc002439bb193cf67891ecadd",
            "language": "en"
        }
        main_url = f"https://newsapi.org/v2/everything?q={trade_entry}&from={from_date}&to={to_date}"
        res = requests.get(main_url, params=query_params)
        open_page = res.json()
        articles = open_page.get("articles", [])
        return articles[:3]
   
    # Function to fetch additional articles on "trading"
    def get_related_articles(from_date, to_date, trade_entry):
        currency1, currency2 = convert_currency_pair_for_api(trade_entry)
        query_params = {
            "apiKey": "44539cbfc002439bb193cf67891ecadd",
            "language": "en"
        }

        main_url = f"https://newsapi.org/v2/everything?q={currency1}&from={from_date}&to={to_date}"
        res = requests.get(main_url, params=query_params)
        open_page = res.json()
        articles = open_page.get("articles", [])
        if not articles:
            main_url = f"https://newsapi.org/v2/everything?q={currency2}&from={from_date}&to={to_date}"
            res = requests.get(main_url, params=query_params)
            open_page = res.json()
            articles = open_page.get("articles", [])

        return articles
   
    # Function to generate summaries
    def generate_summary(article_content):
        prompt = (
            "Please summarize the following news article in a concise manner, "
            "highlighting the key points and main ideas. "
            "Avoid using phrases like 'based on the information I have' or 'I don't have sufficient Information.' even if there is limited information or the news appears truncated. "
            "Here is the article content:\n\n"
            f"{article_content}\n\n"
            "Summary:"
        )
        request_body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.7,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
            body=request_body
        )
        response_body = json.loads(response['body'].read())
        generated_text = response_body['content'][0]['text']
        return generated_text
       
    def total_summary(article_content):
        prompt = (
            "Please summarize the following multiple articles in 4-5 points in a concise manner."
            "The summary should be in numbered points, and each point should be in different lines"
            "highlighting the key points and main ideas. "
            "Text must be properly aligned"
            "Avoid using phrases like 'here is concise summary' or 'based on the information I have' or 'I don't have sufficient Information.' even if there is limited information or the news appears truncated. "
            "Here is the article content:\n\n"
            f"{article_content}\n\n"
            "Summary:"
        )
        request_body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.7,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
            body=request_body
        )
        response_body = json.loads(response['body'].read())
        generated_text = response_body['content'][0]['text']
        return generated_text

    leftPane, emptyPane, rightPane = st.columns([9, 0.5, 5])
   
    article_text = ''
   
    with leftPane:
       
        # Use hardcoded dates
        from_date_str = HARD_CODED_FROM_DATE
        to_date_str = HARD_CODED_TO_DATE
       
        # Load articles related to the hardcoded trade entry and selected dates
        articles = get_trade_articles(TRADE_ENTRY, from_date_str, to_date_str)

        # Define currency pair to yfinance ticker map
        currency_pair_map = {
            'USDHKD': 'HKD=X',
            'USDKRW': 'KRW=X',
            'EURJPY': 'EURJPY=X'
        }
        product_key_slash = ""
        if len(product_key) == 7:
            product_key_slash = product_key[:3] + product_key[4:]
        # Get the correct yfinance ticker
        yf_ticker = currency_pair_map[product_key_slash]
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
            fig1 = px.line(data, x=data.index, y='Close', title=f'{product_key_slash} Hourly Price (Close)',
                        labels={'Close': 'Price', 'index': 'Hour'})
           
            fig1.update_layout(xaxis_title='Time', yaxis_title='Price', template='plotly_dark',
                            title_x=0.25, margin=dict(t=80, l=40, r=40, b=40))
           
            # Plot Volume
            fig2 = px.bar(data, x=data.index, y='Volume', title=f'{product_key_slash} Hourly Trade Volume',
                        labels={'Volume': 'Volume', 'index': 'Hour'})
            fig2.update_layout(xaxis_title='Time', yaxis_title='Volume', template='plotly_dark',
                            title_x=0.25, margin=dict(t=80, l=40, r=40, b=40))

            # Display the Price & volume plot
            st.plotly_chart(fig1)
            st.plotly_chart(fig2)
        else:
            st.write("No yfinance data")
   
    with rightPane:
        # Display each article with its summary and link
        st.markdown("### Related News")
        for article in articles:
            title = article.get("title", "No Title")
            content = article.get("content", "")
            url = article.get("url", "#")
            published_at = article.get("publishedAt", "No Date")
            published_at_formatted = pd.to_datetime(published_at).strftime('%B %d, %Y')
            summary = generate_summary(content)
            article_text  = article_text  + ' Next article: ' + content  
            st.markdown(f"### <span style='color:gray; font-size:12px;'>September 22, 2024</span>", unsafe_allow_html=True)
            with st.expander(f"{title}"):
                st.write(f"{summary}")
                st.write(f"[Read Full Article]({url})")
       
        # If fewer than 5 articles are retrieved, search for related news articles
        if len(articles) < 3:
           
            related_articles = get_related_articles(from_date_str, to_date_str, TRADE_ENTRY)
       
            # Filter related articles where the trade entry is mentioned in the content
            filtered_related_articles = []
            for article in related_articles:
                content = article.get("content", "")
                if article.get("title", "No Title") != '[Removed]':
                    filtered_related_articles.append(article)
                if len(filtered_related_articles) > 2:
                    break
       
            # if len(filtered_related_articles) < 1:
            #     st.markdown(f"### <span style='color:gray; font-size:12px;'>None found</span>", unsafe_allow_html=True)
       
            # Limit related articles to top 5
            for article in filtered_related_articles[:5]:
                title = article.get("title", "No Title")
                description = article.get("description", "")
                url = article.get("url", "#")
                published_at = article.get("publishedAt", "No Date")
                published_at_formatted = pd.to_datetime(published_at).strftime('%B %d, %Y')
                summary = generate_summary(description)
                article_text  = article_text  + ' Next article: ' + description  
                st.markdown(f"### <span style='color:gray; font-size:12px;'>September 22, 2024</span>", unsafe_allow_html=True)
                with st.expander(f"{title}"):
                    st.write(f"{summary}")
                    st.write(f"[Read Full Article]({url})")
                   
                   
                   
        if article_text  != '':
            general_summary = total_summary(article_text)
            st.markdown(
                        f"""
                        <div style='background-color: #F2F1F1; padding: 10px; border-radius: 10px; margin-bottom: 10px;'>
                            <strong>Summary</strong>
                            <p>{general_summary}</p>
                            <div style='display: flex; flex-wrap: wrap;'>
                        """,
                        unsafe_allow_html=True
                    )