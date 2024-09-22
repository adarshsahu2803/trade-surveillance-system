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
        print(product_key)
        TRADE_ENTRY = product_key
    else:
        TRADE_ENTRY = "stocks OR markets OR finance OR trading"

    # Hardcoded trade entry and date range
    HARD_CODED_FROM_DATE = "2024-08-22"
    HARD_CODED_TO_DATE = "2024-09-22"

    # Initialize the Bedrock runtime client
    bedrock_runtime = boto3.client(service_name='bedrock-runtime', aws_access_key_id=access_key,aws_secret_access_key=secret_access_key, region_name='us-east-1')
    
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
    def get_related_articles(from_date, to_date):
        query_params = {
            "apiKey": "0e7d28cbc8244ff1be82e5c884ec67d6",
            "language": "en"
        }

        main_url = f"https://newsapi.org/v2/everything?q=trading&from={from_date}&to={to_date}"
        res = requests.get(main_url, params=query_params)
        open_page = res.json()
        articles = open_page.get("articles", [])
        return articles
    
    # Function to generate summaries
    def generate_summary(article_content):
        prompt = (
            "Please summarize the following news article in a concise manner, "
            "highlighting the key points and main ideas. "
            "Avoid using phrases like 'based on the information I have' or 'I don't have sufficient Information.' "
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
    
    # Initialize the Streamlit app
    st.title(f"Trade News Summaries for {product_key}")

    leftPane, rightPane = st.columns([2,1])
    
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
            st.subheader(f"Number of Articles Mentioning {product_key} Over Time")
            fig = px.line(articles_by_date_full, x='publishedAt', y='Article Count', title=f"Article Count for {product_key} Over Time")
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
            
            related_articles = get_related_articles(from_date_str, to_date_str)
        
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