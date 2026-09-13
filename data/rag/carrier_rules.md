# Carrier Selection Rules

## Rule CR-001: Hazmat Carrier Requirement
- **Condition**: Order has is_hazmat = true OR any item SKU contains "HAZ"
- **Action**: Only carriers with hazmat_certified = true may be selected.
- **Eligible Carriers**: HeavyHaul Freight (CARRIER-HEAVY-02), PrimeExpress Courier (CARRIER-PRIME-04)
- **Violation**: Assigning a non-hazmat-certified carrier to a hazmat shipment is a CRITICAL compliance violation.

## Rule CR-002: Weight Limit Compliance
- **Condition**: Total shipment weight exceeds carrier's max_weight_kg.
- **Action**: Carrier is ineligible. Calculate total weight as sum of (item weight × quantity) for all items.
- **Split Shipment**: If no single carrier can handle total weight, consider splitting into multiple shipments.

## Rule CR-003: Regional Coverage Check
- **Condition**: Shipping destination state is not in carrier's coverage_states list.
- **Action**: Carrier is ineligible unless coverage_states includes "ALL".
- **Example**: EcoTransit Green only covers Midwest states; cannot ship to TX or CA.

## Rule CR-004: Service Level Matching
- **Condition**: Order priority must match an available carrier service level.
- **Mapping**:
  - Order priority "overnight" → carrier must offer "overnight" service
  - Order priority "express" → carrier must offer "express" or "overnight" service
  - Order priority "standard" → any service level acceptable

## Rule CR-005: Cost Optimization
- **When multiple carriers qualify**: Select based on the following priority:
  1. Lowest total shipping cost (base_rate + per_kg × total_weight)
  2. If costs are within 10% of each other: prefer higher reliability_score
  3. If reliability is also similar (within 0.03): prefer faster delivery

## Rule CR-006: Insurance Compatibility
- **Condition**: Order requires insurance (insurance_required = true OR total_value > $1,000).
- **Action**: Include insurance cost in total shipping cost calculation.
- **Formula**: insurance_cost = total_value × (carrier.insurance_rate_percent / 100)

## Rule CR-007: Express Carrier Minimum Reliability
- **Condition**: Order priority is "express" or "overnight".
- **Action**: Carrier reliability_score must be ≥ 0.90. Carriers below this threshold are ineligible for time-sensitive shipments.

## Rule CR-008: Bulk Shipment Handling
- **Condition**: Total shipment weight > 200 kg OR total items > 100 units.
- **Action**: Prefer freight carriers (HeavyHaul Freight) over courier services.
- **Rationale**: Freight carriers offer better per-kg rates for bulk shipments and have infrastructure for large deliveries.
