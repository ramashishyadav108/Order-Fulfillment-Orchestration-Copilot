# Fulfillment Standard Operating Procedures (SOP)

## SOP-001: Order Validation Procedure

### Purpose
Ensure all incoming orders meet minimum requirements before processing.

### Steps
1. **Customer Verification**: Confirm customer_id is valid and non-empty. Cross-reference with customer database.
2. **Address Validation**: Verify shipping address has all required fields (street, city, state, zip, country). US zip codes must be 5 digits.
3. **Item Validation**: Each line item must have a positive quantity (≥ 1) and a valid SKU format (SKU-XXXX-NNN).
4. **Value Check**: Total order value must equal the sum of (quantity × unit_price) for all items. Minimum order value is $10.00.
5. **Date Validation**: Required delivery date must be at least 1 business day from order date. Cannot be more than 90 days in the future.
6. **Hazmat Flag**: If any item SKU contains "HAZ", the is_hazmat flag must be true.

### Rejection Criteria
- Missing or empty customer_id → REJECT with code VAL-001
- Incomplete shipping address → REJECT with code VAL-002
- Negative or zero quantity → REJECT with code VAL-003
- Invalid SKU format → REJECT with code VAL-004
- Value mismatch exceeding $0.01 → REJECT with code VAL-005
- Delivery date in the past → REJECT with code VAL-006

---

## SOP-002: Inventory Allocation Procedure

### Purpose
Allocate inventory from the optimal warehouse(s) to fulfill an order.

### Warehouse Selection Priority
1. **Proximity Rule**: Select the warehouse closest to the shipping destination.
   - East Coast (NJ) → Eastern states
   - Central (TN) → Central states
   - West Coast (CA) → Western states
2. **Stock Availability**: Warehouse must have sufficient unreserved stock (available - reserved ≥ ordered quantity).
3. **Split Fulfillment**: If no single warehouse can fulfill the entire order, split across warehouses starting with the one that can fulfill the most items.

### Allocation Rules
- Reserve stock immediately upon allocation (increment reserved count).
- If total available stock across all warehouses is insufficient, place order on BACKORDER status.
- Never allocate from a warehouse where available quantity would fall below reorder_point after allocation.

---

## SOP-003: Dispatch Procedure

### Purpose
Finalize and dispatch allocated orders.

### Steps
1. Generate dispatch confirmation with unique dispatch_id (DSP-YYYY-NNNN format).
2. Record carrier assignment, tracking number, and estimated delivery.
3. Update inventory: move allocated quantities from reserved to shipped.
4. Notify customer with tracking information.

### Quality Checks Before Dispatch
- Verify carrier is still available and rate has not changed.
- Confirm all items are physically picked and packed.
- Validate shipping label matches order address.
- For hazmat: verify hazmat documentation is attached.

---

## SOP-004: Order Priority Handling

### Priority Levels
- **overnight**: Must be dispatched within 4 hours of order receipt. Use overnight-capable carriers only.
- **express**: Must be dispatched within 8 hours. Use express or overnight carriers.
- **standard**: Must be dispatched within 24 hours. Any carrier service level acceptable.

### Escalation
- If an express/overnight order cannot find a suitable carrier within 2 hours, escalate to supervisor.
- If a standard order is not dispatched within 18 hours, auto-escalate.

---

## SOP-005: Insurance and Value Thresholds

### Rules
- Orders with total_value > $1,000: Insurance REQUIRED regardless of customer preference.
- Orders with total_value > $10,000: Additional signature-on-delivery REQUIRED.
- Hazmat shipments: Insurance ALWAYS required, minimum coverage = 150% of order value.
- Insurance cost = order_value × carrier insurance_rate_percent / 100.
