# Acceptance Criteria

| ID | Criterion | Implemented In |
|---|---|---|
| AC-01 | Built on LangGraph with explicit typed state object (TypedDict/Pydantic) | `src/graph/state.py` |
| AC-02 | Supervisor routes order to specialized worker agents | `src/graph/builder.py`, `src/agents/` |
| AC-03 | Graph uses conditional edges to route on state | `src/graph/routing.py` |
| AC-04 | Node/agent outputs are validated structured objects (Pydantic) | `src/models/*.py`, `BaseAgent._invoke_structured` |
| AC-05 | Checkpointer persists graph state for pause/resume | `src/graph/checkpointer.py` |
| AC-06 | Tiered memory (short-term + long-term/semantic) | `src/memory/` |
| AC-07 | Memory persists across sessions | `src/memory/long_term.py` (tested via `test_memory_persistence.py`) |
| AC-08 | Memory eviction / importance policy | `src/memory/eviction.py` |
| AC-09 | Custom MCP server exposes ≥ 2 tools and 1 resource | `src/mcp/server.py` |
| AC-10 | Agent consumes MCP server via langchain-mcp-adapters | `src/mcp/client.py` |
| AC-11 | Agentic-RAG tool for SOP/rules lookup | `src/rag/`, `src/agents/carrier.py` |
| AC-12 | Reflection or self-healing/fallback loop | `src/agents/reflection.py`, `src/graph/routing.py` |

## Non-Functional Requirements
| ID | Requirement | Implemented In |
|---|---|---|
| NFR-01 | No secrets committed; env-var config | `.env.example`, `src/config/settings.py` |
| NFR-02 | Single command run, README quick-start | `README.md`, `scripts/run_demo.py` |
| NFR-03 | Context quarantine for untrusted text | `src/context/quarantine.py` |
| NFR-04 | Structured JSON logs/traces committed | Generated during tests |
| NFR-05 | All data synthetic; no PII | `data/orders/*.json` |
| NFR-06 | Single-vs-multi decision documented | `docs/framework-decision.md`, `docs/agent-design.md` |
| NFR-07 | Graceful degradation on tool/model failure | `src/mcp/client.py` (fallback tools) |
| NFR-08 | Context-window management (summarization) | `src/context/compressor.py` |
