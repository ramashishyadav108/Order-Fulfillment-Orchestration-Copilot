# Framework Decision: LangGraph vs. CrewAI

## Decision: LangGraph
We selected **LangGraph** over CrewAI for this orchestration capstone.

## Rationale
1. **State Control**: LangGraph provides explicit, typed state control via `TypedDict` and Pydantic. In complex logistics workflows, having a strictly typed state that is passed between nodes is crucial for reliability (AC-01, AC-04).
2. **Conditional Routing**: LangGraph's core abstraction is a graph with conditional edges. This makes it trivial to implement complex routing (e.g., Validation fails -> Route back to Supervisor -> Route to Hold state), which is much harder to express in CrewAI's task-based sequential or hierarchical models (AC-03).
3. **Checkpointing**: LangGraph has native, robust checkpointing (`langgraph-checkpoint-sqlite`). This allows us to pause an order fulfillment process (e.g., waiting for inventory) and resume it later with full state recovery (AC-05).
4. **Self-Healing Loops**: Cycles are native to LangGraph. Our Reflection agent can easily route an order back to the Carrier agent if a rule violation is detected, forming a clean while-loop in the graph execution (AC-12).
