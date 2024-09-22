import streamlit as st
import pandas as pd
import json
import boto3
import requests
from datetime import datetime
import plotly.express as px  
from dotenv import load_dotenv
import os

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
    HARD_CODED_FROM_DATE = "2024-08-24"
    HARD_CODED_TO_DATE = "2024-09-22"

    # Initialize the Bedrock runtime client
    bedrock_runtime = boto3.client(service_name='bedrock-runtime', aws_access_key_id=access_key,aws_secret_access_key=secret_access_key, region_name='us-east-1')
    

    #Convert currency pair to natural language
    def convert_currency_pair_for_api(currency_pair):
    # Dictionary to map currency codes to full names without spaces
        currency_map = {
            'EUR': 'Euro',
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
            "apiKey": "0e7d28cbc8244ff1be82e5c884ec67d6",
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
            "apiKey": "0e7d28cbc8244ff1be82e5c884ec67d6",
            "language": "en"
        }

        main_url = f"https://newsapi.org/v2/everything?q={currency1}&from={from_date}&to={to_date}"
        res = requests.get(main_url, params=query_params)
        open_page = res.json()
        articles = open_page.get("articles", [])
        if not articles:
            main_url = f"https://newsapi.org/v2/everything?q={currency1}&from={from_date}&to={to_date}"
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

    leftPane, emptyPane, rightPane = st.columns([9, 0.5, 5])
    
    with leftPane:
        # Use hardcoded dates
        from_date_str = HARD_CODED_FROM_DATE
        to_date_str = HARD_CODED_TO_DATE
        
        # Load articles related to the hardcoded trade entry and selected dates
        articles = get_trade_articles(TRADE_ENTRY, from_date_str, to_date_str)

        # Prepare data for the graph (number of articles vs. time)
        if articles:
            df = pd.DataFrame(articles)
            df['publishedAt'] = pd.to_datetime(df['publishedAt']).dt.date  # Convert publishedAt to date only
            # Create a date range from from_date to to_date
            full_date_range = pd.date_range(start=from_date_str, end=to_date_str).date
            df_full_dates = pd.DataFrame(full_date_range, columns=['publishedAt'])
        
            # Group articles by published date and count
            articles_by_date = df.groupby('publishedAt').size().reset_index(name='Article Count')
        
            # Merge with the full date range to fill missing dates with zero counts
            articles_by_date_full = pd.merge(df_full_dates, articles_by_date, on='publishedAt', how='left')
            articles_by_date_full['Article Count'].fillna(0, inplace=True)
        
            # Plot line graph with full date range
            st.subheader(f"Trade News Summaries for {product_key}")
            fig = px.line(articles_by_date_full, x='publishedAt', y='Article Count', title=f"Article Count for {product_key} Over Time")
            fig.update_xaxes(title_text="Published On")
            st.plotly_chart(fig)
        else:
            # Create an empty DataFrame for the date range
            full_date_range = pd.date_range(start=from_date_str, end=to_date_str).date
            df_full_dates = pd.DataFrame(full_date_range, columns=['publishedAt'])
            df_full_dates['Article Count'] = 0  # Set Article Count to 0

            st.subheader(f"Trade News Summaries for {product_key}")
            # Plot an empty graph with zeros
            fig = px.line(df_full_dates, x='publishedAt', y='Article Count', title=f"Article Count for {product_key} Over Time (No Articles)")
            fig.update_xaxes(title_text="Published On")
            st.plotly_chart(fig)
    
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
            st.markdown(f"### <span style='color:gray; font-size:12px;'>{published_at_formatted}</span>", unsafe_allow_html=True)
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
                if len(filtered_related_articles) > 3:
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
                st.markdown(f"### <span style='color:gray; font-size:12px;'>{published_at_formatted}</span>", unsafe_allow_html=True)
                with st.expander(f"{title}"):
                    st.write(f"{summary}")
                    st.write(f"[Read Full Article]({url})")