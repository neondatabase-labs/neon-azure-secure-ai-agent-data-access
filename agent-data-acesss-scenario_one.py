import os
import psycopg2
import requests
from datetime import datetime
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, ToolSet
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pprint import pprint
from psycopg2.extras import RealDictCursor


# Load .env file
load_dotenv()

# Initialize Azure AI Project Client
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.environ["PROJECT_CONNECTION_STRING"],
)

# 1. Neon Database Query Tool
def query_finance_data():
    try:
        NEON_DB_URL = os.getenv("NEON_DB_CONNECTION_STRING")
        conn = psycopg2.connect(NEON_DB_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM finance WHERE company = 'IBM'")
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return "No IBM financial records found in the database."
        return "\n".join([str(row) for row in rows])
    except Exception as e:
        return f"❌ Error querying Neon DB: {str(e)}"

# 2. Alpha Vantage API Tool
def fetch_ibm_stock():
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey={os.getenv('ALPHA_VANTAGE_API_KEY')}"
    response = requests.get(url)
    if response.status_code != 200:
        return f"❌ Failed to fetch stock data: {response.status_code}"
    data = response.json().get("Global Quote", {})
    if not data:
        return "No stock data found for IBM."
    return "\n".join([f"{k}: {v}" for k, v in data.items()])

# 3. Serper Search Tool
def search_ibm_news(query="IBM Q4 earnings"):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json"
    }
    payload = {"q": query}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        return f"❌ Serper search error: {response.text}"

    results = response.json().get("organic", [])
    if not results:
        return "No relevant search results found."

    return "\n".join([f"{r['title']} - {r['link']}" for r in results[:3]])

# Shared tools
tools = FunctionTool([search_ibm_news, query_finance_data, fetch_ibm_stock])
toolset = ToolSet()
toolset.add(tools)

# Create Data Collector Agent
data_collector = project_client.agents.create_agent(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    name=f"data-collector-agent-{datetime.now().strftime('%Y%m%d%H%M')}",
    description="Collects financial data from Neon and Alpha Vantage.",
    instructions="""
    You are an AI researcher focused on collecting financial data. Use your tools to:
    - Query Neon Postgres database
    - Fetch IBM stock data from Alpha Vantage
    """,
    toolset=toolset,
)

# Create Data Presenter Agent
data_presenter = project_client.agents.create_agent(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    name=f"data-presenter-agent-{datetime.now().strftime('%Y%m%d%H%M')}",
    description="Presents and summarizes collected financial data.",
    instructions="""
    You are a summarization assistant. Your task is to format and present financial data insights in a concise, readable way.
    """,
    toolset=None  # This agent does not require tools
)

print(f"✅ Agents created:\n- Collector ID: {data_collector.id}\n- Presenter ID: {data_presenter.id}")

# Create thread and run conversation
thread = project_client.agents.create_thread()

# Step 1: Ask data collector to gather financial data
project_client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content="Collect IBM financial records and latest stock data.",
)

collector_run = project_client.agents.create_and_process_run(
    thread_id=thread.id,
    agent_id=data_collector.id,
)
print(f"📥 Data Collector Run Status: {collector_run.status}")

# Step 2: Ask data presenter to summarize collected data
project_client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content="Summarize the financial data collected earlier.",
)

presenter_run = project_client.agents.create_and_process_run(
    thread_id=thread.id,
    agent_id=data_presenter.id,
)
print(f"📝 Data Presenter Run Status: {presenter_run.status}")

# Show final messages
messages = project_client.agents.list_messages(thread_id=thread.id)

messages = messages.get("data", [])
print("\n🧵 Conversation History:\n" + "-" * 60)
for message in reversed(messages):  # Reverse to show in time order
    role = message["role"]
    timestamp = datetime.fromtimestamp(message["created_at"]).strftime('%Y-%m-%d %H:%M:%S')
    content = message["content"][0]["text"]["value"]
    assistant_id = message.get("assistant_id")
    # Determine who spoke
    if role == "user":
        speaker = "🧑 User"
    elif role == "assistant":
        speaker = f"🤖 Agent ({assistant_id or 'Unknown'})"
    else:
        speaker = f"❓ {role}"
    print(f"{speaker} at {timestamp}")
    print("-" * len(f"{speaker} at {timestamp}"))
    print(content.strip())
    print("-" * 60)