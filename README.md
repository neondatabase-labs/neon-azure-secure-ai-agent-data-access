# Secure Data Access for AI Agents

This project demonstrates how to **securely connect AI agents to multiple data sources** using [Azure AI Agent Service](https://learn.microsoft.com/en-us/azure/ai-services/agents/overview). It showcases real-world scenarios where agents must access financial data responsibly — with row-level restrictions, limited views, and masked outputs — depending on the user's access rights.

Inspired by concepts in [this article](), this project explores **data-aware AI agents** that interact with APIs, databases, and the web, while respecting dynamic access controls.

---

## 🧠 What This Project Demonstrates

This repo implements a secure, multi-source AI agent system that:

- Connects to **Neon serverless Postgres** to retrieve financial records
- Uses **Alpha Vantage API** to fetch live stock data
- Leverages **Serper.dev** for real-time internet search (e.g., IBM earnings)
- Enforces **role-based data access** for users via `user_roles.yaml`
- Differentiates access levels like:
  - 🔒 Row-level restricted views
  - 🔍 Limited column views
  - 👶️ Masking sensitive data like revenue/profit
  - ❌ API restriction scenarios

Each role-specific scenario is handled automatically through Azure AI Agents, ensuring secure and controlled data interactions for AI applications.

---

## ✨ Features

- 🧹 **Two-agent collaboration**: Collector + Presenter
- 🌐 **Multi-source orchestration** with DB + APIs + Web
- 🔐 **Secure access enforcement** via roles
- 🧱 **Toolset-based architecture** for modular extensibility
- 💬 **Thread-based memory** between agents in Azure AI Agent Service
- ☁️ **Postgres (Neon) + OpenAI + Web Search** all in one flow

---

## 📦 Prerequisites

Before you start, make sure you have:

- Python 3.9+
- An Azure subscription - [Create one for free](https://azure.microsoft.com/free/cognitive-services).
- Make sure you have the Azure AI Developer [RBAC role](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-azure-ai-foundry) assigned.
- Neon Serverless Postgres on Azure. Install it from the [Azure Marketplace](https://azuremarketplace.microsoft.com/en-us/marketplace/apps/neon1722366567200.neon_serverless_postgres_azure_prod?tab=overview) for free.
- API keys:
  - [Alpha Vantage API](https://www.alphavantage.co/support/) free API access
  - [Serper API](https://serper.dev/) free API access

---

## ⚙️ Setup Instructions

### 1. Create a **Neon Database on Azure**

Open the [new Neon Resource page](https://portal.azure.com/#view/Azure_Marketplace_Neon/NeonCreateResource.ReactView) on the Azure portal, and it brings up the form to create a Neon Serverless Postgres Resource. Fill out the form with the required fields and deploy it. 

#### Obtain Neon Database Credentials

1. After the resource is created, go to the Neon Serverless Postgres Organization service and click on the Portal URL. This brings you to the Neon Console
2. Click “New Project”
3. Choose an Azure region
4. Give your project a name (e.g., “Postgres AI Agent”)
5. Click “Create Project”
6. Once the project is created successfully, copy the Neon connection string and note down. You can find the connection details in the Connection Details widget on the Neon Dashboard.

```bash
    postgresql://[user]:[password]@[neon_hostname]/[dbname]?sslmode=require
```

### 2. Create an AI Foundry Project on Azure

Create a new hub and project in the Azure AI Foundry portal by [following the guide](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart?pivots=ai-foundry-portal#create-a-hub-and-project-in-azure-ai-foundry-portal) in the Microsoft docs. You also need to [deploy a model](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart?pivots=ai-foundry-portal#deploy-a-model) like GPT-4o. 

You only need the **Project connection string** and **Model Deployment Name** from the Azure AI Foundry portal. You can also find your connection string in the **overview** for your project in the [**Azure AI Foundry portal**](https://ai.azure.com/), under **Project details** > **Project connection string**.

Once you have all three values on hand: **Neon connection string**, **Project connection string,** and **Model Deployment Name,** you are ready to set up the Python project to create an Agent from [Python SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme?view=azure-python-preview).


### 3. Clone the repo and install dependencies
```bash
git clone https://github.com/your-org/billing-anomaly-agent.git
cd neon-azure-secure-ai-agent-data-access
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate for Windows
pip install -r requirements.txt
```

### 4. Environment Setup

Create a `.env` file in the root directory:

```env
NEON_DATABASE_URL=your_neon_connection_string
PROJECT_CONNECTION_STRING=your_azure_project_connection_string
AZURE_OPENAI_DEPLOYMENT_NAME=your_azure_openai_model
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
SERPER_API_KEY=your_serper_api_key
```

---

## 🚀 Usage

### Database Setup
To set up the Neon database with sample financial data, run:
```
python neondb_setup.py
```

### Run Data Access Scenarios
You can run the two scripts to see various scenarios based on the article

```
python agent-data-acesss-scenario_one.py
python agent-data-acesss-scenarios_limited.py
```

Roles will be read from `user_roles.yaml`, and the appropriate data access level will be automatically enforced.

Example user roles:

```yaml
users:
  - username: user_a
    roles:
      - admin
      - full_data_access
  - username: user_b
    roles: #comment each row for each scenario in the article
      - restricted
      - limited_api_access
      - restricted_db
      - row_restricted
      - mask_data
```

---

## 🧠 Scenario Highlights

| Scenario           | What Happens                                                   |
|--------------------|----------------------------------------------------------------|
| **Full Access**     | Agent can see all DB data and fetch API stock prices          |
| **Row-Restricted**  | Agent only sees rows tagged as `'restricted'`                |
| **Column-Limited**  | Agent only gets `company` and `stock_price`                  |
| **Masked Output**   | Presenter hides revenue/profit before summarizing            |
| **API Blocked**     | Agent skips external API fetch task                          |

These simulate real-world business constraints for **compliance, internal roles, or customer tiering**.

---

## 🧹 Folder Structure

```
📁 neon-azure-secure-ai-agent-data-access
🔸 agent-data-acesss-scenario_one.py      
🔸 agent-data-acesss-scenarios_limited.py
🔸 neondb_setup.py                     
🔸 user_roles.yaml                    
🔸 .env_example                          
🔸 requirements.txt
🔸 README.md
```

---

## 📋 Related Concepts

- [Azure AI Agents (Foundry)](https://learn.microsoft.com/en-us/azure/ai-services/agents/)
- [Neon Postgres](https://neon.tech)
---

## ⚖️ License

MIT License — free to use, extend, and share.

---

## 🤝 Contributing

We welcome PRs! If you want to add new data sources, access patterns, or tool integrations, submit an issue or pull request.

