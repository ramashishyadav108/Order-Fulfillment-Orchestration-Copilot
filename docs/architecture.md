# System Architecture

## Overview
The Order Fulfillment Copilot is built on a modular, multi-agent architecture using LangGraph. It leverages a custom MCP server for system integration, a FAISS-backed RAG system for rule retrieval, and a tiered memory system for persistence and context management.

## Components

### 1. Agent Orchestration (LangGraph)
- **State**: A typed `FulfillmentState` (using Pydantic models) shared across all nodes.
- **Topology**: A Supervisor-Worker topology. The Supervisor evaluates the current state and routes to the appropriate specialized worker (Validation, Inventory, Carrier, Dispatch, Reflection).
- **Checkpointing**: SQLite-backed checkpointer allows the graph to be paused, resumed, and inspected.

### 2. Context Engineering Layer
- **Writer**: Structures raw JSON into tagged, agent-consumable text.
- **Selector**: Filters context so each agent only sees what it needs (e.g., Validation doesn't see carrier rates).
- **Compressor**: Summarizes long threads to manage context windows.
- **Quarantine**: Isolates untrusted free-text (customer notes) to prevent prompt injection.

### 3. Tiered Memory System
- **Short-Term (Working)**: Fast, in-memory dictionary for the current session with LRU eviction.
- **Long-Term (Persistent)**: SQLite database storing facts and decisions across sessions.
- **Semantic**: FAISS vector store embedding memory contents for similarity search.
- **Eviction Policy**: A composite policy weighting importance, recency, and access frequency, with a hard TTL override.

### 4. Integration (MCP & RAG)
- **MCP Server**: A custom stdio server exposing `inventory_lookup` and `carrier_rates` tools.
- **RAG System**: A FAISS index over markdown SOPs, providing on-demand rule lookups for the Carrier agent.
