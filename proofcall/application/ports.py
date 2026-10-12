"""Ports the application needs from the outside world."""
from __future__ import annotations

from typing import Any, Dict, List, Protocol


class LanguageModel(Protocol):
    def complete(self, system: str, messages: List[Dict[str, str]]) -> str:
        """Return the model's text (JSON expected by callers)."""


class ToolBackend(Protocol):
    def call(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool; return variables to set ({name: value}) plus optional 'message'."""


class Clock(Protocol):
    def now(self) -> float:
        """Monotonic seconds."""
