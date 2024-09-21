from flask import Flask, request, jsonify
import boto3
import sqlalchemy
from sqlalchemy import create_engine, text
import pymysql
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# RDS connection parameters from environment variables
rds_host = os.getenv('RDS_HOST')
rds_port = 3306
rds_user = os.getenv('RDS_USER')
rds_password = os.getenv('RDS_PASSWORD')
rds_db_name = os.getenv('RDS_DB_NAME')

# Initialize Bedrock client
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

def convert_to_sql_bedrock(natural_language_query):
    prompt = f"""
    Human: Convert the following natural language query into SQL for a MySQL database. Make sure the SQL is accurate. This query is directly being passed into the RDS table for querying so only give the SQL query; you should not give anything else.
    Based on the query given by the user, choose the appropriate table name from the details given below. The table and schema are given in the format table_name:Attributes.
    1)front_running: Product, ProductKey, AlertID, Ageing, AlertCreationDate, AlertDate, OrderNotional, RiskScoreIndicator, Trader, Step.
    2)insider_trading: Product,ProductKey,AlertID,TradeType,OrderNotional,RiskScoreIndicator,TraderEmail,TradeTime
    3)ramping:Product,ProductKey,AlertID,RampType,PriceChange,VolumeChange,TraderEmail,AlertDate
    4)layering:Product,ProductKey,AlertID,LayeringType,OrderSize,OrderPrice,TraderEmail,AlertDate
    5)spoofing:Product,ProductKey,AlertID,SpoofingType,OrderSize,OrderPrice,TraderEmail,Timestamp

    Only the SQL query needs to be generated, no additional text since it directly goes to MySQL.
    Natural Language Query: "{natural_language_query}"

    SQL Query:
    Assistant:
    """
    
    # Prepare the input for the Bedrock model
    input_data = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000
    }
    
    response = bedrock_client.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
        body=json.dumps(input_data),
        contentType='application/json',
        accept='application/json'
    )
    
    # Extract the SQL query from the response
    response_body = json.loads(response['body'].read().decode('utf-8'))
    sql_query = response_body.get('content', [{}])[0].get('text', '').strip()
    return sql_query

def convert_to_natural_language_bedrock(natural_language_query, result_text):
    prompt = f"""
    Human: Convert the following SQL query result into a natural language response by taking in the given input below. Give the response in such a way that the result of the SQL query is communicated to the user who gave the natural query and no aspect of the SQL statement is involved in the response. Only give the response, do not give any other extra response like brackets etc just the sql statement.
    Natural Language Query: "{natural_language_query}"
    SQL Query Result: "{result_text}"

    Combined Response:
    Assistant:
    """
    
    # Prepare the input for the Bedrock model
    input_data = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000
    }
    
    response = bedrock_client.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
        body=json.dumps(input_data),
        contentType='application/json',
        accept='application/json'
    )
    
    # Extract the combined response from the response
    response_body = json.loads(response['body'].read().decode('utf-8'))
    combined_response = response_body.get('content', [{}])[0].get('text', '').strip()
    return combined_response

def connect_to_rds():
    try:
        engine = create_engine(f'mysql+pymysql://{rds_user}:{rds_password}@{rds_host}:{rds_port}/{rds_db_name}')
        return engine
    except Exception as e:
        print(f"Error connecting to RDS: {e}")
        return None

def execute_sql_query(engine, sql_query):
    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            rows = result.fetchall()
            return rows
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return None

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    natural_language_query = data.get('query')
    
    if not natural_language_query:
        return jsonify({"error": "No query provided"}), 400
    
    # Step 1: Convert natural language to SQL using Bedrock and Claude 3.5
    sql_query = convert_to_sql_bedrock(natural_language_query)
    print(f"Generated SQL Query: {sql_query}")
    
    # Step 2: Connect to RDS
    engine = connect_to_rds()
    if not engine:
        return jsonify({"error": "Failed to connect to RDS"}), 500
    
    # Step 3: Execute the SQL query
    results = execute_sql_query(engine, sql_query)
    
    # Step 4: Process and return the results
    if results:
        result_text = "Query Results:\n"
        for row in results:
            result_text += ", ".join(map(str, row)) + "\n"
        print(result_text)
        
        # Step 5: Convert SQL query result back to natural language with combined response
        combined_response = convert_to_natural_language_bedrock(natural_language_query, result_text)
        print(f"Combined Response: {combined_response}")
        
        return jsonify({"result": result_text, "combined_response": combined_response})
    else:
        return jsonify({"error": "No results found or query execution failed"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
