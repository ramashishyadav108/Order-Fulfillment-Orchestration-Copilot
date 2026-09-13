
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.config import settings


# Maximum context size before compression triggers (in characters)
COMPRESSION_THRESHOLD = 8000
COMPRESSED_TARGET_SIZE = 3000


class ContextCompressor:

    def __init__(self, llm: Optional[ChatGoogleGenerativeAI] = None):
        self._llm = llm

    @property
    def llm(self) -> ChatGoogleGenerativeAI:
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.0,
            )
        return self._llm

    def should_compress(self, context: Dict[str, Any]) -> bool:
        context_str = json.dumps(context, default=str)
        return len(context_str) > COMPRESSION_THRESHOLD

    def compress(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.should_compress(context):
            return context

        compressed = {}

        # Always preserve metadata and order summary unchanged
        for key in ["metadata", "order_summary", "shipping", "errors"]:
            if key in context:
                compressed[key] = context[key]

        # Summarize verbose sections
        verbose_sections = {}
        for key in context:
            if key not in compressed:
                verbose_sections[key] = context[key]

        if verbose_sections:
            summary = self._summarize_sections(verbose_sections)
            compressed["compressed_history"] = summary
            compressed["_compression_metadata"] = {
                "original_size": len(json.dumps(context, default=str)),
                "compressed_size": len(json.dumps(compressed, default=str)),
                "sections_compressed": list(verbose_sections.keys()),
            }

        return compressed

    def _summarize_sections(self, sections: Dict[str, Any]) -> str:
        try:
            sections_text = json.dumps(sections, default=str, indent=2)

            messages = [
                SystemMessage(content=(
                    "You are a context compression assistant. Summarize the following "
                    "fulfillment processing data into a concise paragraph. Preserve all "
                    "key facts: order IDs, statuses, allocated quantities, carrier names, "
                    "costs, errors, and decisions. Remove redundant details."
                )),
                HumanMessage(content=f"Compress this context:\n{sections_text}"),
            ]

            response = self.llm.invoke(messages)
            return response.content[:COMPRESSED_TARGET_SIZE]
        except Exception as e:
            # Fallback: truncate instead of summarize
            return json.dumps(sections, default=str)[:COMPRESSED_TARGET_SIZE] + "... [truncated]"

    def compress_message_history(self, messages: List[Dict]) -> List[Dict]:
        if len(messages) <= 6:
            return messages

        # Keep last 4 messages intact
        recent = messages[-4:]
        older = messages[:-4]

        # Summarize older messages
        older_text = "\n".join(
            f"[{m.get('role', 'unknown')}]: {m.get('content', '')[:200]}"
            for m in older
        )

        summary_msg = {
            "role": "system",
            "content": (
                f"[Compressed history of {len(older)} earlier messages]: "
                f"{self._summarize_text(older_text)}"
            ),
        }

        return [summary_msg] + recent

    def _summarize_text(self, text: str) -> str:
        try:
            messages = [
                SystemMessage(content="Summarize the following conversation history concisely, preserving key decisions and facts."),
                HumanMessage(content=text[:4000]),
            ]
            response = self.llm.invoke(messages)
            return response.content[:1000]
        except Exception:
            return text[:1000] + "... [truncated]"
