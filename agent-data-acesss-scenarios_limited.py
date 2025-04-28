import os
import psycopg2
import requests
import yaml
from datetime import datetime
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, ToolSet
from azure.identity import DefaultAzureCredential
from pprint import pprint

# Load environment variables
load_dotenv()

NEON_DB_URL = os.getenv("NEON_DB_CONNECTION_STRING")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Initialize Azure AI Project client
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.environ["PROJECT_CONNECTION_STRING"],
)

# -----------------------------------
# Tools definitions
# -----------------------------------

def query_finance_data():
    """Query all finance data from Neon."""
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM finance")
        rows = cursor.fetchall()
        conn.close()
        return "\n".join([str(row) for row in rows]) if rows else "No finance data found."
    except Exception as e:
        return f"❌ Error querying Neon: {str(e)}"

def query_limited_finance_data():
    """Query limited finance data (company and stock price only) from Neon."""
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT company, stock_price FROM finance")
        rows = cursor.fetchall()
        conn.close()
        return "\n".join([str(row) for row in rows]) if rows else "No limited finance data found."
    except Exception as e:
        return f"❌ Error querying Neon: {str(e)}"

def query_row_level_finance_data():
    """Query row level restricted finance data from Neon."""
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM finance WHERE user_role = 'restricted'")
        rows = cursor.fetchall()
        conn.close()
        return "\n".join([str(row) for row in rows]) if rows else "No row level restricted data found."
    except Exception as e:
        return f"❌ Error querying Neon: {str(e)}"

def fetch_financial_data():
    """Fetch IBM financial data from Alpha Vantage API."""
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get("Global Quote", {})
        return "\n".join([f"{k}: {v}" for k, v in data.items()]) if data else "No stock data found."
    return f"❌ API error: {response.text}"

def search_ibm_news(query="IBM Q4 earnings"):
    """Search IBM financial news using Serper API."""
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"q": query}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        results = response.json().get("organic", [])
        return "\n".join([f"{r['title']} - {r['link']}" for r in results[:3]])
    return f"❌ Serper API error: {response.text}"

# -----------------------------------
# YAML user role logic
# -----------------------------------

def get_user_roles(username):
    with open('user_roles.yaml', 'r') as file:
        users = yaml.safe_load(file)['users']
    for user in users:
        if user['username'] == username:
            return user['roles']
    return []

# -----------------------------------
# Azure Agent creation
# -----------------------------------

# Create toolset
toolset = ToolSet()
toolset.add(FunctionTool([search_ibm_news, query_finance_data, fetch_financial_data]))

# Create Data Collector Agent
data_collector = project_client.agents.create_agent(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    name=f"data-collector-{datetime.now().strftime('%Y%m%d%H%M')}",
    description="Collects IBM financial data from Neon, APIs, and Web.",
    instructions="Use your tools to collect financial and stock data related to IBM.",
    toolset=toolset,
)

# Create Data Presenter Agent
data_presenter = project_client.agents.create_agent(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    name=f"data-presenter-{datetime.now().strftime('%Y%m%d%H%M')}",
    description="Formats and summarizes collected financial data.",
    instructions="Summarize the financial data collected earlier into a nice report.",
)

# -----------------------------------
# Communication flow
# -----------------------------------

# Create conversation thread
thread = project_client.agents.create_thread()

# Set current user
current_user = "user_b"
roles = get_user_roles(current_user)

# Dynamic tasks
print("\n🛠️ Configuring tasks based on user roles...\n")

# Internet search task
project_client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content="Search for IBM's Q4 financial results from the web.",
)
project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=data_collector.id)

# Finance database task
if "restricted_db" in roles:
    query_task = "Query limited finance data"
    query_tool = "query_limited_finance_data"
elif "row_restricted" in roles:
    query_task = "Query row level restricted finance data"
    query_tool = "query_row_level_finance_data"
else:
    query_task = "Query full finance data"
    query_tool = "query_finance_data"

project_client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content=f"{query_task} from the Neon database.",
)
project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=data_collector.id)

# Financial API task (only if allowed)
if "limited_api_access" not in roles:
    project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="Fetch IBM's latest stock data from Alpha Vantage.",
    )
    project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=data_collector.id)

# Data presenter task
if "mask_data" in roles:
    present_instruction = "Summarize the financial data but mask revenue and profit."
else:
    present_instruction = "Summarize the collected financial data into a clean report."

project_client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content=present_instruction,
)
project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=data_presenter.id)

# -----------------------------------
# Display results
# -----------------------------------

# Fetch messages
messages_response = project_client.agents.list_messages(thread_id=thread.id)
messages = messages_response.get("data", [])

print("\n📨 Final Summary:\n" + "=" * 60)
for msg in reversed(messages):
    role = msg["role"]
    content = msg["content"][0]["text"]["value"]
    sender = "🤖 Assistant" if role == "assistant" else "🧑 User"
    print(f"{sender}: {content}\n" + "-" * 60)
