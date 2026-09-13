# Warehouse Allocation Rules

## Rule WR-001: Geographic Proximity Assignment
Assign orders to the nearest warehouse based on shipping destination:

| Destination Region | Primary Warehouse | Secondary Warehouse | Tertiary Warehouse |
|---|---|---|---|
| Northeast (NY, NJ, PA, CT, MA, etc.) | WH-EAST-01 | WH-CENTRAL-01 | WH-WEST-01 |
| Southeast (FL, GA, NC, SC, VA, etc.) | WH-EAST-01 | WH-CENTRAL-01 | WH-WEST-01 |
| Midwest (IL, OH, MI, IN, WI, etc.) | WH-CENTRAL-01 | WH-EAST-01 | WH-WEST-01 |
| South Central (TX, OK, AR, LA, etc.) | WH-CENTRAL-01 | WH-WEST-01 | WH-EAST-01 |
| Mountain (CO, AZ, NM, UT, etc.) | WH-WEST-01 | WH-CENTRAL-01 | WH-EAST-01 |
| Pacific (CA, OR, WA, etc.) | WH-WEST-01 | WH-CENTRAL-01 | WH-EAST-01 |

## Rule WR-002: Stock Availability Check
Before allocation:
1. Check `quantity_available - reserved` for each SKU at the target warehouse.
2. If available stock ≥ ordered quantity: allocate from this warehouse.
3. If available stock < ordered quantity: check secondary and tertiary warehouses.

## Rule WR-003: Split Fulfillment Protocol
When no single warehouse can fulfill the complete order:
1. Allocate maximum available from the primary warehouse.
2. Allocate remainder from secondary warehouse.
3. If still insufficient, allocate from tertiary warehouse.
4. If total available across all warehouses < ordered quantity: mark order as BACKORDER.
5. Each split creates a separate shipment with its own tracking.

## Rule WR-004: Reorder Point Protection
- Never allocate stock that would bring available quantity below the reorder_point.
- Effective available = quantity_available - reserved - reorder_point.
- If effective available ≤ 0: warehouse is considered OUT OF STOCK for that SKU.

## Rule WR-005: Hazmat Warehouse Restrictions
- Hazmat items (SKUs containing "HAZ") can only be stored/shipped from warehouses with hazmat storage capability.
- Currently certified warehouses: WH-EAST-01, WH-WEST-01.
- WH-CENTRAL-01 does NOT have hazmat certification; cannot fulfill hazmat orders.

## Rule WR-006: Consolidation Preference
- Prefer fulfilling all items from a single warehouse to minimize shipments.
- Split fulfillment adds 15% to total shipping cost due to multiple shipments.
- Only split when consolidation is impossible due to stock constraints.

## Rule WR-007: Peak Season Capacity
During peak season (November 15 - December 31):
- Each warehouse has a daily dispatch capacity limit of 500 orders.
- If capacity is reached, route to the next available warehouse.
- Priority orders (express/overnight) get reserved capacity of 20% of daily limit.
