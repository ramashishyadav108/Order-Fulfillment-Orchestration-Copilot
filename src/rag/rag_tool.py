
from __future__ import annotations
import json
from typing import List
from langchain_core.tools import Tool

from src.rag.retriever import RagRetriever


def get_rag_tools() -> List[Tool]:
    retriever = RagRetriever()
    
    return [
        Tool(
            name="lookup_fulfillment_sop",
            description=(
                "Look up rules in the Fulfillment Standard Operating Procedures (SOP). "
                "Use this to answer questions about validation rules, prioritization, "
                "or general fulfillment process requirements. Input is a search query string."
            ),
            func=retriever.retrieve_sop,
        ),
        Tool(
            name="lookup_carrier_rules",
            description=(
                "Look up specific carrier selection rules. "
                "Use this to understand constraints around hazmat, weight limits, "
                "service levels, and cost optimization. Input is a search query string."
            ),
            func=retriever.retrieve_carrier_rules,
        ),
        Tool(
            name="lookup_warehouse_rules",
            description=(
                "Look up warehouse allocation rules. "
                "Use this to understand geographic routing, stock checks, and "
                "split fulfillment protocols. Input is a search query string."
            ),
            func=retriever.retrieve_warehouse_rules,
        ),
    ]
