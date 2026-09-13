# RAG System Design

## Overview
The system implements Agentic RAG to allow agents (specifically the Carrier Agent) to look up complex business rules dynamically, rather than stuffing all rules into the system prompt.

## Components

### 1. Document Loader (`src/rag/documents.py`)
- Reads Markdown files from `data/rag/` (SOPs, Carrier Rules, Warehouse Rules).
- Splits documents into logical chunks based on Markdown headers (`##`).
- Preserves metadata (source file, section title) for citation.

### 2. Vector Store (`src/rag/vector_store.py`)
- Uses **FAISS** (Facebook AI Similarity Search) as an efficient, local, in-memory vector database.
- Uses **BAAI/bge-small-en-v1.5** via `sentence-transformers` for high-quality, lightweight text embeddings.
- Persists the index locally to `runtime/rag/faiss_index/`.

### 3. Agent Integration (`src/rag/rag_tool.py`)
- Exposes specific lookup tools to the LangChain agents (e.g., `lookup_carrier_rules`).
- The agent *decides* when to use the tool based on the complexity of the order (e.g., if `is_hazmat=True`, it queries the tool for hazmat rules).
