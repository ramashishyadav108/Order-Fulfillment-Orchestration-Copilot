
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.manager import MemoryManager
from src.models.memory import MemoryTier

logging.basicConfig(level=logging.INFO)

def main():
    print("="*60)
    print("TESTING CROSS-SESSION MEMORY PERSISTENCE (AC-07)")
    print("="*60)
    
    # Session 1: Store a fact
    session1_id = "test-session-001"
    print(f"\n--- Starting Session 1 ({session1_id}) ---")
    mem1 = MemoryManager(session_id=session1_id)
    
    fact_key = "customer_preference_alpha"
    fact_content = "Customer Alpha requires dock delivery and no weekend shipments."
    
    print(f"Storing fact: '{fact_content}'")
    mem1.store(
        key=fact_key,
        content=fact_content,
        tier=MemoryTier.LONG_TERM,
        importance=0.9
    )
    
    print("Session 1 complete. Memory manager destroyed.")
    del mem1
    
    # Simulate time passing/restart
    print("\n... Simulating system restart ...\n")
    
    # Session 2: Recall the fact
    session2_id = "test-session-002"
    print(f"--- Starting Session 2 ({session2_id}) ---")
    mem2 = MemoryManager(session_id=session2_id)
    
    print(f"Attempting to recall fact with key: {fact_key}")
    recalled = mem2.recall(fact_key)
    
    if recalled:
        print(f"SUCCESS! Recalled fact: '{recalled}'")
        if recalled == fact_content:
            print("Fact matches perfectly across sessions. AC-07 verified.")
        else:
            print("Fact content mismatch!")
    else:
        print("FAILED! Could not recall fact across sessions.")
        
    print("\n="*60)

if __name__ == "__main__":
    main()
