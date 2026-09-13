
from __future__ import annotations
import json
import warnings
from typing import Any, Dict, List, Optional, Type, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, ValidationError

from src.config import settings
from src.context.manager import ContextManager
from src.models.agent import AgentRole



T = TypeVar("T", bound=BaseModel)

# Suppress known non-critical warnings from Google GenAI SDK
# warnings.filterwarnings("ignore", message=".*fixed sampling defaults.*")
# warnings.filterwarnings("ignore", message=".*Direct use of automatic function calling.*")


class BaseAgent:

    def __init__(
        self,
        role: AgentRole,
        context_manager: Optional[ContextManager] = None,
        llm: Optional[ChatGoogleGenerativeAI] = None,
    ):
        self.role = role
        self.context_manager = context_manager or ContextManager()
        self.llm = llm or ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )

    def _invoke_structured(
        self,
        prompt: str,
        output_schema: Type[T],
        system_prompt: Optional[str] = None,
        session_id: str = "default_session",
    ) -> T:
        sys_prompt = system_prompt or self.context_manager.get_system_prompt(self.role)

        # Use json_schema method — direct JSON generation, no function-calling/AFC
        structured_llm = self.llm.with_structured_output(
            output_schema, method="json_schema"
        )

        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=prompt),
        ]

        try:
            print("%s agent invoking LLM (json_schema mode)" % self.role.value)
            print("*"*80)
            print("LLM called")
            result = structured_llm.invoke(messages)
            print(result)
            
            return result
        except ValidationError as e:
            print("%s agent validation error: %s" % (self.role.value, e))
            raise
        except Exception as e:
            print("%s agent invocation error: %s" % (self.role.value, e))
            raise

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement process()")
