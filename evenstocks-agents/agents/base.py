"""Base agent abstraction — all analyst/manager agents inherit from this."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from anthropic import Anthropic

from config import settings


@dataclass
class AgentResult:
    agent_name: str
    report: str
    confidence: float = 0.5
    error: Optional[str] = None


class BaseAgent(ABC):
    name: str = "base"
    model: str = settings.DEEP_MODEL
    max_tokens: int = 1500

    def __init__(self):
        self._client: Optional[Anthropic] = None

    @property
    def client(self) -> Anthropic:
        if self._client is None:
            self._client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    @abstractmethod
    def system_prompt(self) -> str:
        ...

    @abstractmethod
    def user_prompt(self, context: dict) -> str:
        ...

    def run(self, context: dict) -> AgentResult:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt(),
                messages=[{"role": "user", "content": self.user_prompt(context)}],
            )
            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            return AgentResult(agent_name=self.name, report=text.strip())
        except Exception as exc:
            return AgentResult(
                agent_name=self.name,
                report="",
                error=f"{type(exc).__name__}: {exc}",
            )
