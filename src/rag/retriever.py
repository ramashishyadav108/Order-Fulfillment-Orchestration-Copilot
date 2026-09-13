
from __future__ import annotations
from typing import List, Optional

from src.rag.vector_store import RagVectorStore


class RagRetriever:
    
    def __init__(self, vector_store: Optional[RagVectorStore] = None):
        self.vector_store = vector_store or RagVectorStore()
        
    def retrieve_sop(self, query: str, top_k: int = 2) -> str:
        results = self.vector_store.search(query, top_k=top_k, source_filter="fulfillment_sop")
        return self._format_results(results, "Fulfillment SOP")
        
    def retrieve_carrier_rules(self, query: str, top_k: int = 2) -> str:
        results = self.vector_store.search(query, top_k=top_k, source_filter="carrier_rules")
        return self._format_results(results, "Carrier Rules")
        
    def retrieve_warehouse_rules(self, query: str, top_k: int = 2) -> str:
        results = self.vector_store.search(query, top_k=top_k, source_filter="warehouse_rules")
        return self._format_results(results, "Warehouse Rules")
        
    def _format_results(self, results: List, source_name: str) -> str:
        if not results:
            return f"No relevant information found in {source_name}."
            
        formatted = [f"--- Relevant Extracts from {source_name} ---"]
        for chunk, score in results:
            formatted.append(f"\n[{chunk.title}] (relevance: {score:.2f})")
            formatted.append(chunk.content)
            
        return "\n".join(formatted)
