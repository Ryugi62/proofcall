"""Per-call variable store: every value remembers where it came from."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Tuple


class VariableStore:
    def __init__(self) -> None:
        self._values: Dict[str, Tuple[Any, str]] = {}

    def set(self, name: str, value: Any, source: str) -> None:
        self._values[name] = (value, source)

    def update_from_tool(self, values: Dict[str, Any]) -> None:
        for k, v in values.items():
            self.set(k, v, source="tool")

    def get(self, name: str) -> Optional[Any]:
        item = self._values.get(name)
        return None if item is None else item[0]

    def has(self, name: str) -> bool:
        return name in self._values

    def has_prefix(self, prefix: str, source: str = "tool") -> bool:
        return any(k.startswith(prefix) and src == source for k, (_, src) in self._values.items())

    def values_from(self, source: str) -> Iterable[Any]:
        return [v for (v, src) in self._values.values() if src == source]

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        return {k: {"value": v, "source": s} for k, (v, s) in sorted(self._values.items())}
