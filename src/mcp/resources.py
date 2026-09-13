"""
MCP Resource implementations for the fulfillment domain.
"""

from __future__ import annotations
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def get_fulfillment_sop() -> str:
    """
    MCP Resource 1: Return the fulfillment SOP document.
    
    Provides the standard operating procedures for order fulfillment
    including validation, allocation, dispatch, priority handling, and insurance rules.
    """
    sop_path = DATA_DIR / "rag" / "fulfillment_sop.md"
    if sop_path.exists():
        return sop_path.read_text(encoding="utf-8")
    return "Fulfillment SOP document not found."


def get_carrier_rules() -> str:
    """Return carrier selection rules document."""
    rules_path = DATA_DIR / "rag" / "carrier_rules.md"
    if rules_path.exists():
        return rules_path.read_text(encoding="utf-8")
    return "Carrier rules document not found."


def get_warehouse_rules() -> str:
    """Return warehouse allocation rules document."""
    rules_path = DATA_DIR / "rag" / "warehouse_rules.md"
    if rules_path.exists():
        return rules_path.read_text(encoding="utf-8")
    return "Warehouse rules document not found."
