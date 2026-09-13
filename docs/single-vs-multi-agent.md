# Single vs Multi-Agent Architecture

This document outlines the architectural decisions for the Order Fulfillment Orchestration Copilot, specifically comparing a Single Agent design to our implemented Multi-Agent design.

## Single Agent Architecture
In a single-agent approach, one large LLM is responsible for the entire fulfillment process: parsing the order, validating rules, checking inventory, selecting a carrier, and dispatching.

**Pros:**
- Simpler graph architecture (often just one node).
- Easier to manage conversational state (one prompt loop).

**Cons:**
- **Prompt Size Explosion**: All business rules (validation, routing, carrier selection) must fit into a single system prompt, leading to context bloat and degraded performance.
- **Hallucination Risk**: The model may blend rules (e.g., applying inventory logic to carrier selection).
- **Hard to Test**: Debugging a single monolithic decision process is complex.

## Multi-Agent Architecture (Our Implementation)
We implemented a Multi-Agent architecture using LangGraph (Supervisor, Validation, Inventory, Carrier, Dispatch, Reflection).

**Pros:**
- **Specialization**: Each agent has a focused system prompt and schema (e.g., `CarrierAgent` only knows about carrier rules).
- **Reliability & Modularity**: Easy to swap out or test individual agents. Errors in one node don't corrupt the entire state.
- **Guardrails (NFR-07)**: We can place programmatic constraints between agent boundaries. The deterministic Supervisor routing prevents infinite LLM reasoning loops.
- **Traceability**: Node transitions and structured outputs at each boundary make it easy to log, trace, and audit the fulfillment pipeline.

**Cons:**
- Higher initial setup complexity (LangGraph routing).
- State management overhead (must explicitly merge context between agents).

**Conclusion:** The multi-agent approach is far superior for complex, rule-heavy workflows like order fulfillment, ensuring high reliability and auditability.
