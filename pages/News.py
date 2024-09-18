import streamlit as st
import pandas as pd
import json
import boto3
import requests
from datetime import datetime, timedelta
import plotly.express as px  
 
# Hardcoded trade entry
TRADE_ENTRY = "USDJPY"
 
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
 
# Function to generate summaries using the provided code
def generate_summary(article_content):
    prompt = "Summarize the following news article: " + article_content
    print(prompt)
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
 
# Date inputs for filtering articles
default_start = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')  # Default to yesterday
default_end = datetime.now().strftime('%Y-%m-%d')  # Default to today
 
# Initialize the Streamlit app
st.title(f"Trade News Summaries for {TRADE_ENTRY.upper()}")
 
dateCol1, dateCol2 = st.columns(2)
 
with dateCol1:
    from_date = st.date_input("From Date", value=pd.to_datetime(default_start))
 
with dateCol2:
    to_date = st.date_input("To Date", value=pd.to_datetime(default_end))
 
# Convert dates to string format expected by the API
from_date_str = from_date.strftime('%Y-%m-%d')
to_date_str = to_date.strftime('%Y-%m-%d')
 
# Load articles related to the hardcoded trade entry and selected dates
articles = get_trade_articles(TRADE_ENTRY, from_date_str, to_date_str)
 
# Initialize the Bedrock runtime client
bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
 
# Prepare data for the graph (number of articles vs. time)
 
# Prepare data for the graph (number of articles vs. time)
if articles:
    df = pd.DataFrame(articles)
    df['publishedAt'] = pd.to_datetime(df['publishedAt']).dt.date  # Convert publishedAt to date only
    # Create a date range from from_date to to_date
    full_date_range = pd.date_range(start=from_date, end=to_date).date
    df_full_dates = pd.DataFrame(full_date_range, columns=['publishedAt'])
 
    # Group articles by published date and count
    articles_by_date = df.groupby('publishedAt').size().reset_index(name='Article Count')
 
    # Merge with the full date range to fill missing dates with zero counts
    articles_by_date_full = pd.merge(df_full_dates, articles_by_date, on='publishedAt', how='left')
    articles_by_date_full['Article Count'].fillna(0, inplace=True)
 
    # Plot line graph with full date range
    st.subheader(f"Number of Articles Mentioning {TRADE_ENTRY.upper()} Over Time")
    fig = px.line(articles_by_date_full, x='publishedAt', y='Article Count', title=f"Article Count for {TRADE_ENTRY.upper()} Over Time")
    st.plotly_chart(fig)
# Display each article with its summary and link
for article in articles:
 
    title = article.get("title", "No Title")
    content = article.get("content", "")
    url = article.get("url", "#")
    published_at = article.get("publishedAt", "No Date")  # Get publication date
    print(content)
    # Format the date
    published_at_formatted = pd.to_datetime(published_at).strftime('%B %d, %Y')
    summary = generate_summary(content)
    # Use markdown to format the title and date
    st.markdown(f"### <span style='color:gray; font-size:12px;'>{published_at_formatted}</span>", unsafe_allow_html=True)
    with st.expander(f"{title}"):
        st.write(f"{summary}")
        st.write(f"[Read Full Article]({url})")
 
# If fewer than 5 articles are retrieved, search for related news articles
if len(articles) < 3:
    st.markdown("### Related News")
    related_articles = get_related_articles(from_date_str, to_date_str)
 
    # Filter related articles where the trade entry is mentioned in the content
    filtered_related_articles = []
    for article in related_articles:
        content = article.get("content", "")
        if TRADE_ENTRY.lower() in content.lower():
            filtered_related_articles.append(article)
        if len(filtered_related_articles)>4:
            break
 
    if len(filtered_related_articles) < 1:
        st.markdown(f"### <span style='color:gray; font-size:12px;'>None found</span>", unsafe_allow_html=True)
 
    # Limit related articles to top 5
    for article in filtered_related_articles[:5]:
        title = article.get("title", "No Title")
        description = article.get("description", "")
        url = article.get("url", "#")
        published_at = article.get("publishedAt", "No Date")  # Get publication date
        # Format the date
        published_at_formatted = pd.to_datetime(published_at).strftime('%B %d, %Y')
        summary = generate_summary(description)
        # Use markdown to format the title and date
        st.markdown(f"### <span style='color:gray; font-size:12px;'>{published_at_formatted}</span>", unsafe_allow_html=True)
        with st.expander(f"{title}"):
            st.write(f"{summary}")
            st.write(f"[Read Full Article]({url})")