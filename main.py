"""
main.py — Single entry point for the Order Fulfillment Orchestration Copilot.

Usage examples:
  python main.py --order data/orders/sample_order_001.json   # Process one order
  python main.py --demo                  # Process all 4 sample orders
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Fix Windows console encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

# Suppress non-critical SDK UserWarning messages
import warnings
warnings.filterwarnings("ignore", message=".*fixed sampling defaults.*")
warnings.filterwarnings("ignore", message=".*Direct use of automatic function calling.*")
warnings.filterwarnings("ignore", message=".*Deserializing unregistered type.*")

# Colour helpers
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}[OK] {msg}{RESET}")
def fail(msg): print(f"  {RED}[FAIL] {msg}{RESET}")
def info(msg): print(f"  {CYAN}[INFO] {msg}{RESET}")
def warn(msg): print(f"  {YELLOW}[WARN] {msg}{RESET}")
def section(title):
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")


def process_order_file(order_file: str, thread_id: str = None) -> bool:
    section(f"PROCESS ORDER: {Path(order_file).name}")

    file_path = Path(order_file)
    if not file_path.exists():
        fail(f"Order file not found: {file_path}")
        return False

    with open(file_path) as f:
        order_data = json.load(f)

    info(f"Order ID: {order_data.get('order_id')}")
    info(f"Customer: {order_data.get('customer_name')}")
    info(f"Priority: {order_data.get('priority')}")
    info(f"Items: {len(order_data.get('items', []))}")
    info(f"Is Hazmat: {order_data.get('is_hazmat')}")

    # Validate API key
    from src.config import settings
    if not settings.GOOGLE_API_KEY:
        fail("GOOGLE_API_KEY not set. Create a .env file from .env.example")
        return False

    thread = thread_id or f"thread-{order_data.get('order_id', 'unknown')}"

    try:
        from src.application.service import FulfillmentService
        service = FulfillmentService(session_id="demo-session")
        final = service.process_order(order_data, thread_id=thread)

        # Display results
        raw_status = final.get("status", "unknown")
        status_str = raw_status.value if hasattr(raw_status, "value") else str(raw_status)

        print(f"\n  ┌── Final Status: {BOLD}{status_str.upper()}{RESET}")

        if final.get("validation_result"):
            vr = final["validation_result"]
            v_valid = vr.get("is_valid") if isinstance(vr, dict) else vr.is_valid
            print(f"  │  Validation:  {'✔ Passed' if v_valid else '✘ Failed'}")

        if final.get("allocation_result"):
            ar = final["allocation_result"]
            a_status = (ar.get("status") if isinstance(ar, dict) else ar.status.value)
            print(f"  │  Allocation:  {a_status}")

        if final.get("carrier_result"):
            cr = final["carrier_result"]
            carrier_name = (cr.get("selected_carrier_name") if isinstance(cr, dict)
                            else getattr(cr, "selected_carrier_name", None))
            cost = (cr.get("total_cost") if isinstance(cr, dict)
                    else getattr(cr, "total_cost", None))
            print(f"  │  Carrier:     {carrier_name or 'None'} (${cost:.2f})" if cost else
                  f"  │  Carrier:     {carrier_name or 'None'}")

        if final.get("dispatch_result"):
            dr = final["dispatch_result"]
            dispatch_id = (dr.get("dispatch_id") if isinstance(dr, dict)
                           else getattr(dr, "dispatch_id", "?"))
            print(f"  │  Dispatch ID: {dispatch_id}")

        if final.get("reflection_result"):
            rr = final["reflection_result"]
            severity = (rr.get("severity") if isinstance(rr, dict)
                        else getattr(rr, "severity", "?"))
            confidence = (rr.get("confidence_score") if isinstance(rr, dict)
                          else getattr(rr, "confidence_score", 0))
            print(f"  │  Reflection:  severity={severity}, confidence={confidence:.2f}")

        if final.get("errors"):
            for e in final["errors"]:
                print(f"  │  ⚠ Error: {e}")

        print(f"  └──────────────────────────────")
        ok(f"Order {order_data.get('order_id')} processed - status: {status_str}")
        return True

    except Exception as e:
        fail(f"Order processing failed: {e}")
        traceback.print_exc()
        return False


def run_demo():
    section("DEMO: All Sample Orders")
    orders_dir = ROOT / "data" / "orders"
    results = {}

    for i in range(1, 5):
        fname = f"sample_order_00{i}.json"
        fpath = orders_dir / fname
        if fpath.exists():
            success = process_order_file(str(fpath), thread_id=f"demo-thread-{i}")
            results[fname] = "✔ OK" if success else "✘ FAILED"
        else:
            results[fname] = "⚠ NOT FOUND"

    print(f"\n{BOLD}Demo Summary:{RESET}")
    for fname, res in results.items():
        print(f"  {res}  {fname}")


def main():
    parser = argparse.ArgumentParser(
        description="Order Fulfillment Orchestration Copilot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--demo", action="store_true", help="Process all sample orders")
    parser.add_argument("--order", type=str, help="Path to an order JSON file")

    args = parser.parse_args()

    # Default to demo if no arguments provided
    if not any(vars(args).values()):
        run_demo()
        return

    if args.order:
        process_order_file(args.order)

    if args.demo:
        run_demo()


if __name__ == "__main__":
    main()
