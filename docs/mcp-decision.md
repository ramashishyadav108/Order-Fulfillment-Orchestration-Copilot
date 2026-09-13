# MCP Integration Decision

## Rationale for MCP vs. Direct API / DB
We chose to implement system integrations (WMS Inventory, Carrier Rate APIs) via the **Model Context Protocol (MCP)** rather than direct API calls or direct database connections.

### Why MCP?
1. **Separation of Concerns**: The MCP server encapsulates the domain logic for inventory calculation (handling reserved vs. available vs. reorder points) and carrier rate logic. The LangGraph agents don't need to know how to calculate these; they just consume the standardized MCP tool.
2. **Standardization**: By using the MCP stdio protocol, the tool implementations are completely decoupled from the LangChain agent framework. 
3. **Interoperability**: The same MCP server could easily be consumed by Claude Desktop or another agent framework without modification.
4. **Security**: The agent only has access to the specific tools exposed by the MCP server, acting as a secure boundary.

## Implementation Details
- **Server**: `src/mcp/server.py` implements the MCP stdio server exposing two tools (`inventory_lookup`, `carrier_rates`) and one resource (`fulfillment_sop`).
- **Adapter**: `src/mcp/client.py` uses `langchain-mcp-adapters` to dynamically load these tools into LangChain format for the Gemini agents.
- **Graceful Degradation** (NFR-07): If the MCP server subprocess fails to start, the client falls back to direct Python implementations of the tools to ensure the system remains functional.
