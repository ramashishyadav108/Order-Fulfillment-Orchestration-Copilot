
import argparse
import json
from pathlib import Path
import sys

from src.application.service import FulfillmentService
from src.config import settings

# Setup basic logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def run_cli(order_file: str, thread_id: str = "test-thread-1"):
    file_path = Path(order_file)
    if not file_path.exists():
        print(f"Error: Order file not found at {file_path}")
        sys.exit(1)
        
    with open(file_path, "r") as f:
        order_data = json.load(f)
        
    print(f"Processing order from {file_path.name}...")
    service = FulfillmentService(session_id="cli-session")
    
    result = service.process_order(order_data, thread_id=thread_id)
    
    print("\n" + "="*50)
    print("FINAL RESULT")
    print("="*50)
    print(f"Status: {result.get('status')}")
    if result.get('errors'):
        print(f"Errors: {result['errors']}")
    print("="*50)


def main():
    parser = argparse.ArgumentParser(description="Order Fulfillment Copilot")
    parser.add_argument("--order", type=str, help="Path to order JSON file")
    parser.add_argument("--ui", action="store_true", help="Launch Streamlit UI")
    
    args = parser.parse_args()
    
    if args.ui:
        import subprocess
        print("Launching Streamlit UI...")
        # Path to a separate streamlit app file we will create
        # subprocess.run(["streamlit", "run", "src/application/ui.py"])
        print("UI not yet implemented in this snippet")
    elif args.order:
        run_cli(args.order)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
