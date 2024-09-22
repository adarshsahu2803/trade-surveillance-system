import streamlit as st
import boto3
import pandas as pd
import pymysql
from transformers import AutoTokenizer, AutoModelForCausalLM
import json
import re
import os
from dotenv import load_dotenv

# S3 and RDS Configuration
bucket_name = 'topgun4-tsas'
s3_file_key = 'Alerts Data.csv'
rds_host = 'tsas-db.c5i8sasy23wv.us-east-1.rds.amazonaws.com'
rds_user = 'admin'
rds_passwd = 'tsasdbpass'
rds_db = 'alerts_data_db'
access_key = os.getenv('ACCESS_KEY_ID')
secret_access_key = os.getenv('SECRET_ACCESS_KEY')

st.write(access_key)
st.write(secret_access_key)

# Set up Bedrock runtime client (Make sure AWS credentials are configured)
bedrock_runtime = boto3.client('bedrock-runtime',aws_access_key_id=access_key,aws_secret_access_key=secret_access_key, region_name='us-east-1')

def load_data_from_s3(file_name):
    """Download the dataset from S3 and return a Pandas DataFrame."""
    s3_client = boto3.client('s3')
    try:
        # Corrected string formatting for the S3 file and local file name
        s3_client.download_file(bucket_name, f'{file_name}.csv', f'{file_name}.csv')
        df = pd.read_csv(f'{file_name}.csv')
        return df
    except boto3.exceptions.NoCredentialsError:
        st.error("AWS credentials not found. Please configure your credentials.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

def connect_to_rds():
    """Connect to the AWS RDS MySQL database."""
    conn = pymysql.connect(host=rds_host, user=rds_user, password=rds_passwd, db=rds_db)
    return conn

def execute_sql_query(query, conn):
    """Execute an SQL query and return the results."""
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    # Convert the results to a pandas DataFrame
    df = pd.DataFrame(results, columns=[col[0] for col in cursor.description])
    return df

def translate_to_sql(natural_language_query):
    """Convert natural language query to SQL using a pre-trained model."""
    model_name = "Salesforce/codegen-350M-mono"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    
    input_text = f"Generate SQL for the query: {natural_language_query}"
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True)
    outputs = model.generate(inputs["input_ids"], max_length=100, num_beams=5, early_stopping=True)
    
    sql_query = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return sql_query

# Function to get summary from Bedrock using the product key
def get_summary(product_key):
        # Load Excel data from S3
        st.write("hello")
        df = pd.read_excel('s3://topgun4-tsas/Orderlifecycle-scenario1.xlsx')
        st.write("bye")
        df = df[df['Product Key'] == product_key]

        # Add row numbers
        df['RowNumber'] = df.index

        # Convert DataFrame to JSON
        data_as_text = df.to_json(orient='records')

        # Create the prompt for the model
        prompt = f"Given the following JSON input - {data_as_text} containing a product key - {product_key}, summarize the key details and provide a concise overview. Give output as text with meaningful context."

        # Create request body for the model
        request_body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 3000,
            "temperature": 0.7,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })

        # Invoke the Claude model
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
            body=request_body
        )

        # Read and decode the response
        streaming_body = response['body']
        body_content = streaming_body.read()
        body_text = body_content.decode('utf-8')

        # Parse the JSON response
        body_json = json.loads(body_text)

        # Log the full response for debugging
        # print("Full response from model:", body_json)

        # Check if 'content' key is present in the response
        if 'content' in body_json:
            output = body_json['content'][0]['text']
            
            # Remove unnecessary patterns from the output
            pattern = r"Based on the provided JSON input, "
            modified_text = re.sub(pattern, '', output)

            return modified_text
        else:
            return f"Error: 'content' key not found in the response. Full response: {body_json}"


        # Remove unnecessary patterns from the output
        pattern = r"Based on the provided JSON input, "
        modified_text = re.sub(pattern, '', output)

        return modified_text