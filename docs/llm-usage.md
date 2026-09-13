# LLM Invocation & Architecture Documentation

This document describes all Large Language Model (LLM) calls in the Order Fulfillment Orchestration Copilot: which model is called, when it is triggered, what data is sent to it, and what work it performs.

---

## 1. Overview & Model Setup

- **Model**: Google Gemini (`gemini-2.0-flash-lite` by default, configurable via `GEMINI_MODEL` in `.env`).
- **Client**: `ChatGoogleGenerativeAI` from `langchain_google_genai`.
- **Invocation Pattern**: Centralized in [`src/agents/base.py`](file:///c:/Users/ray09/Music/airdawg-document/capstone2/src/agents/base.py) inside `BaseAgent._invoke_structured()`.
- **Output Mode**: `json_schema` mode via LangChain `with_structured_output(output_schema, method="json_schema")`. This guarantees type-safe Pydantic models with zero manual parsing errors.

---

## 2. Quick Summary Table

| Step | Agent / Component | When Called | What is Sent | Work Performed | Output Schema |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **ValidationAgent** | Stage 1 (Order Ingestion) | Order summary, shipping address, line items, business rules | Validates order integrity & consistency against business rules | `OrderValidationResult` |
| **2** | **InventoryAgent** | Stage 2 (Post-Validation) | Order context + raw JSON from MCP `inventory_lookup` tool | Determines stock allocation across warehouses or triggers backorder | `AllocationResult` |
| **3** | **CarrierAgent** | Stage 3 (Post-Inventory) | Order context + MCP `carrier_rates` + RAG carrier compliance rules | Selects cheapest, compliant carrier (checking hazmat, SLAs, reliability) | `CarrierSelectionResult` |
| **4** | **DispatchAgent** | Stage 4 (Post-Carrier) | Full fulfillment context (allocation & carrier details) | Creates dispatch records, assigns tracking numbers and delivery dates | `DispatchResult` |
| **5** | **ReflectionAgent** | Stage 5 (Post-Dispatch) | Full pipeline context & results + audit checklist | Audits entire fulfillment for SLA, cost, and compliance anomalies | `ReflectionResult` |
| **Aux** | **ContextCompressor** | When context > 8,000 chars | Verbose state history in JSON | Summarizes old context down to ≤ 3,000 chars while preserving facts | Plain text summary |

---

## 3. Detailed Agent Breakdown

### 1. Validation Agent
- **File**: [`src/agents/validation.py`](file:///c:/Users/ray09/Music/airdawg-document/capstone2/src/agents/validation.py)
- **When Called**: First execution node in the LangGraph workflow after order receipt (`Supervisor -> ValidationNode`).
- **What is Sent**:
  - **System Prompt**: Role instructions to validate customer ID, shipping completeness, quantities (≥1), unit prices (>0), delivery date validity, hazmat SKU detection, and total calculation match.
  - **Prompt Data**:
    - Order summary (order_id, customer_id, dates, total_value, priority)
    - Shipping address (street, city, state, zip)
    - Line items (SKU, quantity, unit_price)
    - Specific business checklist rules
- **Work Performed**: Evaluates business constraints and flags any discrepancies or syntax/integrity errors.
- **Output Schema**: `OrderValidationResult`
  - `order_id`: string
  - `is_valid`: bool
  - `errors`: list of error messages (empty if valid)
  - `warnings`: list of non-fatal warnings

---

### 2. Inventory Agent
- **File**: [`src/agents/inventory.py`](file:///c:/Users/ray09/Music/airdawg-document/capstone2/src/agents/inventory.py)
- **When Called**: Triggered when `ValidationAgent` confirms `is_valid = True`.
- **Pre-LLM Action**: Invokes MCP tool `inventory_lookup` for the order's SKUs to retrieve real-time stock levels.
- **What is Sent**:
  - **System Prompt**: Instructions to allocate inventory applying proximity rules, reorder thresholds, and split fulfillment rules.
  - **Prompt Data**:
    - Order context & shipping destination state
    - Raw inventory JSON from the MCP `inventory_lookup` tool (effective stock across warehouses)
    - Allocation logic rules (prefer closest warehouse, split if insufficient, backorder if total stock is lacking)
- **Work Performed**: Reasons over warehouse inventory levels vs destination location and determines the optimal allocation plan.
- **Output Schema**: `AllocationResult`
  - `order_id`: string
  - `status`: `allocated` | `split_fulfillment` | `backordered` | `failed`
  - `allocations`: list of `{sku, warehouse_id, quantity, unit_cost}`
  - `warehouses_used`: list of warehouse IDs
  - `is_split`: bool
  - `shortages`: list of missing item SKUs (if any)

---

### 3. Carrier Agent
- **File**: [`src/agents/carrier.py`](file:///c:/Users/ray09/Music/airdawg-document/capstone2/src/agents/carrier.py)
- **When Called**: Triggered when inventory has been successfully allocated.
- **Pre-LLM Actions**:
  1. Invokes MCP tool `carrier_rates` with package weight, destination state, service level, hazmat flag, and order value.
  2. Invokes RAG tool `lookup_carrier_rules` against FAISS vector store to fetch relevant shipping compliance guidelines.
- **What is Sent**:
  - **System Prompt**: Instructions to choose the optimal carrier optimizing for cost while honoring SLA and hazmat certifications.
  - **Prompt Data**:
    - Order context (weight, priority, destination)
    - Live rates from MCP `carrier_rates`
    - Regulatory policies retrieved from RAG
    - Optimization rules (hazmat compliance CR-001, service level CR-004, reliability score threshold CR-007, cost minimization CR-005)
- **Work Performed**: Evaluates eligible carriers against constraints and rates to select the best carrier.
- **Output Schema**: `CarrierSelectionResult`
  - `order_id`: string
  - `selected_carrier_id`: string (or null if none eligible)
  - `selected_carrier_name`: string
  - `service_level`: string
  - `base_rate`, `fuel_surcharge`, `hazmat_surcharge`, `total_cost`: float
  - `estimated_days`: int
  - `is_hazmat_compliant`: bool
  - `selection_reason`: detailed justification string

---

### 4. Dispatch Agent
- **File**: [`src/agents/dispatch.py`](file:///c:/Users/ray09/Music/airdawg-document/capstone2/src/agents/dispatch.py)
- **When Called**: Triggered after carrier selection succeeds.
- **What is Sent**:
  - **System Prompt**: Instructions to create final dispatch records, tracking numbers, and confirm carrier assignments.
  - **Prompt Data**:
    - Order details, allocated warehouses from `allocation_result`, and selected carrier data from `carrier_result`.
    - Instructions to format tracking numbers, estimate delivery date, and calculate total costs.
- **Work Performed**: Generates formal dispatch records, assigns realistic tracking IDs per warehouse shipment, and marks the order ready for shipping.
- **Output Schema**: `DispatchResult`
  - `order_id`: string
  - `dispatch_id`: string (format `DSP-YYYY-XXXXXX`)
  - `shipments`: list of `{shipment_id, warehouse_id, carrier_id, tracking_number, estimated_delivery}`
  - `is_dispatched`: bool (`True`)
  - `total_shipping_cost`: float
  - `total_insurance_cost`: float
  - `notes`: string

---

### 5. Reflection Agent
- **File**: [`src/agents/reflection.py`](file:///c:/Users/ray09/Music/airdawg-document/capstone2/src/agents/reflection.py)
- **When Called**: Final agent node in the pipeline after dispatch record generation.
- **What is Sent**:
  - **System Prompt**: Instructions to review end-to-end fulfillment quality, checking for SLA breaches, cost anomalies, or compliance failures.
  - **Prompt Data**:
    - Full cumulative order state: validation status, inventory allocation, carrier choice, dispatch records, errors, and memory context.
    - 6-point review checklist (validation status, stock allocation, carrier eligibility, hazmat compliance, dispatch status, cost sanity).
- **Work Performed**: Conducts an automated post-fulfillment audit. Decides whether the order is completed cleanly or requires self-healing/reprocessing.
- **Output Schema**: `ReflectionResult`
  - `order_id`: string
  - `severity`: `none` | `low` | `medium` | `high` | `critical`
  - `recommendation`: `complete` | `select_carrier` | `allocate_inventory` | `hold` | `human_review`
  - `issues_found`: list of string descriptions
  - `corrective_actions`: list of suggested remedial steps
  - `confidence_score`: float (0.0 to 1.0)
  - `needs_reprocessing`: bool

---

### 6. Context Compressor (Auxiliary / Conditional)
- **File**: [`src/context/compressor.py`](file:///c:/Users/ray09/Music/airdawg-document/capstone2/src/context/compressor.py)
- **When Called**: Dynamically invoked only if the context payload passed between agents exceeds 8,000 characters.
- **What is Sent**:
  - **System Prompt**: "You are a context compression assistant. Summarize the following fulfillment processing data into a concise paragraph. Preserve all key facts..."
  - **Prompt Data**: The verbose historical fields in JSON format.
- **Work Performed**: Condenses historical state down to ≤ 3,000 characters to protect LLM context windows and reduce token latency.
- **Output**: Compressed text summary placed under `context["compressed_history"]`.

---

## 4. Non-LLM Components (Clarification)

To avoid confusion during log inspection:
1. **SupervisorAgent** ([`src/agents/supervisor.py`](file:///c:/Users/ray09/Music/airdawg-document/capstone2/src/agents/supervisor.py)):
   - Does **NOT** call an LLM.
   - Uses a deterministic state-machine lookup (`_STATUS_TO_ACTION`) for fast, predictable routing.
2. **Embeddings & Vector Search** ([`src/rag/vector_store.py`](file:///c:/Users/ray09/Music/airdawg-document/capstone2/src/rag/vector_store.py)):
   - Does **NOT** call an LLM API.
   - Uses a local sentence-transformer model (`BAAI/bge-small-en-v1.5`) running locally via FAISS.
