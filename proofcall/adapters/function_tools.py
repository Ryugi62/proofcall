"""ToolBackend that executes the exported in-call function sources themselves (what is tested = what is shipped).
Results are namespaced as variables `<tool>.<key>`; the spoken `say` text is also stored as `<tool>.say`."""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from .export import callkaro_functions


class FunctionTools:
    def __init__(self, config: Dict[str, Any], catalog: Dict[str, Any], context: Dict[str, Any] = None):
        self.context = context or {"current_time": "2026-10-13T10:00:00+05:30", "user_phone_number": "910000000000"}
        self.sources = callkaro_functions(config, catalog)
        self.fns = {}
        for fname, src in self.sources.items():
            ns: Dict[str, Any] = {"tool": lambda f: f, "x_context": self.context}
            exec(compile(src, f"callkaro_functions/{fname}", "exec"), ns)
            self.fns[fname[:-3]] = ns[fname[:-3]]
        self.loop = asyncio.new_event_loop()

    def call(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        fn = self.fns.get(name)
        if fn is None:
            return {"message": f"unknown tool {name}", f"{name}.ok": False}
        try:
            out = self.loop.run_until_complete(fn(**{k: v for k, v in (args or {}).items()}))
        except TypeError as e:          # wrong arguments from the model
            return {"message": f"bad arguments: {e}", f"{name}.ok": False}
        result = {f"{name}.{k}": (", ".join(map(str, v)) if isinstance(v, list) else v) for k, v in out.items()}
        result["message"] = out.get("say", "")
        return result
