
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.application.runner import run_cli


def main():
    data_dir = Path(__file__).parent.parent / "data" / "orders"
    
    orders = [
        "sample_order_001.json",
        "sample_order_002.json",
        "sample_order_003.json",
        "sample_order_004.json"
    ]
    
    for i, order in enumerate(orders):
        order_path = data_dir / order
        if order_path.exists():
            print(f"\n{'='*80}")
            print(f"RUNNING DEMO FOR {order}")
            print(f"{'='*80}\n")
            run_cli(str(order_path), thread_id=f"demo-thread-{i}")
        else:
            print(f"Order file not found: {order_path}")


if __name__ == "__main__":
    main()
