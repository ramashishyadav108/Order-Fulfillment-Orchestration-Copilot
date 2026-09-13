# Agent Design and Patterns

## Multi-Agent Orchestration
We utilize a **Supervisor-Worker** pattern implemented via LangGraph. 
- **Rationale**: Fulfillment is a sequential but highly conditional process. A single massive agent would suffer from prompt bloat and confused priorities. A supervisor routing to specialized workers ensures separation of concerns, cleaner prompts, and easier testing of individual domains (validation vs. carrier selection).

## Agent Implementations

### Base Agent
All agents inherit from a `BaseAgent` that enforces structured output using LangChain's `with_structured_output` (Pydantic validation). This guarantees that handoffs between nodes are well-formed (AC-04).

### The Workers (ReAct Pattern)
- **Inventory Agent**: Uses a simplified ReAct pattern. It first calls the MCP `inventory_lookup` tool, incorporates the tool's JSON output into its prompt, and then reasons over the data to produce an `AllocationResult`.
- **Carrier Agent**: Uses a ReAct pattern with multiple tools. It calls the MCP `carrier_rates` tool and can optionally query the `lookup_carrier_rules` RAG tool if complex hazmat or regional rules apply.

### Reflection and Self-Healing
- **Reflection Agent**: After dispatch, this agent reviews the entire state. If it detects anomalies (e.g., exorbitant shipping costs relative to order value), it sets `needs_reprocessing = True` and recommends routing back to a previous stage (e.g., `SELECT_CARRIER`), creating a self-healing loop (AC-12).
