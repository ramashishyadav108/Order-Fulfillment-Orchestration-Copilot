# Order Fulfillment Orchestration Copilot 🤖📦

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Framework](https://img.shields.io/badge/framework-LangGraph-orange)
![LLM](https://img.shields.io/badge/LLM-Gemini_Pro-green)

A sophisticated, multi-agent AI copilot designed to fully automate and orchestrate the supply chain order fulfillment process.This project demonstrates advanced agentic patterns including dynamic routing, context engineering, tiered memory, and Model Context Protocol (MCP) integrations.

---

## ✨ Key Features

- **Multi-Agent Architecture**: Built on LangGraph, utilizing a specialized Supervisor agent to dynamically route orders to specialized sub-agents (Validation, Inventory, Carrier, Dispatch) based on real-time fulfillment status.
- **Context Engineering Pipeline**: Implements strict data isolation. Includes a `ContextQuarantine` module to actively sanitize untrusted user text (preventing prompt injections) before it reaches the agents.
- **Tiered Memory System**: 
  - *Short-Term*: Ephemeral graph state during order processing.
  - *Long-Term*: SQLite-backed persistent memory across sessions.
  - *Semantic*: FAISS-backed dense vector memory with an automated, importance-weighted eviction policy.
- **Custom MCP Server**: Provides strict, typed tools (`inventory_lookup`, `carrier_rates`) and business resources to the agents seamlessly.
- **Agentic RAG**: FAISS-powered retrieval augmented generation for agents to autonomously consult Standard Operating Procedures (SOPs) and carrier rules mid-execution.
- **Self-Healing Reflection**: A Reflection agent performs post-execution QA on every order, capable of re-routing the workflow backward if it detects logic errors.

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11 or higher
- A Google Gemini API Key

### 2. Installation
Clone the repository and set up your environment:
```bash
# Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Copy the environment template and add your Gemini API key:
```bash
cp .env.example .env
```
Open `.env` and set:
`GOOGLE_API_KEY="your_api_key_here"`

### 4. Build the Knowledge Base (RAG)
Before the agents can consult the fulfillment guidelines, you must build the local FAISS index:
```bash
python scripts/build_rag.py
```

## 🎮 Running the System

### The Full Demo
The easiest way to see the multi-agent system in action is to run the automated demo, which processes 4 distinct synthetic scenarios:
```bash
python main.py
```

### Processing a Single Order
To process a specific JSON order file through the pipeline:
```bash
python main.py --order data/orders/sample_order_001.json
```

## 🧪 Synthetic Data Scenarios

The system includes four pre-configured scenarios designed to stress-test different agent capabilities:

| Order File | Scenario Description | Key Agents Triggered |
|------------|----------------------|----------------------|
| `sample_order_001.json` | **Happy Path** - Standard, valid order. | All agents |
| `sample_order_002.json` | **Malicious Input** - Missing fields and attempted prompt injection. | Quarantine, Validation |
| `sample_order_003.json` | **Split Fulfillment** - Large order triggering a stock-out and multi-warehouse allocation. | Inventory (MCP) |
| `sample_order_004.json` | **Hazmat Handling** - Dangerous goods requiring specialized carrier selection and SOP retrieval. | Carrier (RAG) |

## 📊 Generating Evidence

To automatically generate the JSON proofs and execution traces required by the capstone grading rubric (AC-01 through AC-12):
```bash
python scripts/run_evidence.py
```
This will output all necessary rubric proofs directly into the `evidence/` directory.

---
*Built for the Agentic AI Capstone.*
