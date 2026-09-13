# Memory System Design

The system implements a tiered memory architecture to handle immediate context, persistent facts, and semantic search (AC-06).

## Tier 1: Short-Term (Working) Memory
- **Implementation**: In-memory `OrderedDict`.
- **Purpose**: Fast access to the current session's state and recent turns.
- **Eviction**: Simple LRU when capacity (e.g., 100 items) is reached. Cleared on process exit.

## Tier 2: Long-Term Memory
- **Implementation**: SQLite database (`runtime/memory/memory.db`).
- **Purpose**: Persists critical facts (e.g., "Order 001 was allocated to WH-EAST") across sessions (AC-07).
- **Access**: Key-value lookup and SQL querying by session or order ID.

## Tier 3: Semantic Memory
- **Implementation**: FAISS vector index using BGE-small embeddings.
- **Purpose**: Enables agents to recall past decisions based on similarity rather than exact keys.

## Eviction Policy (AC-08)
The `EvictionManager` uses a composite policy:
1. **TTL Override**: Any memory older than its Time-To-Live (e.g., 7 days) is immediately evicted.
2. **Importance-Weighted Scoring**: Remaining memories are scored based on:
   - `importance` (0.0 - 1.0, set at creation)
   - `recency` (time since last access)
   - `frequency` (number of times accessed)
3. **Threshold**: When total items exceed `max_entries`, the lowest-scoring memories are evicted first.
