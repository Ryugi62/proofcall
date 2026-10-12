"""Re-audit a finished call transcript (e.g. exported from the voice platform) with the deterministic auditor.

Input turns: [{"role": "agent"|"customer", "text": str, "functions": [{"name", "args", "result"}]}]
Function results are namespaced into the variable store exactly as in the live engine (`<function>.<key>`), so a
claim is backed only if a function in this call actually returned the value."""
from __future__ import annotations

from typing import Any, Dict, List

from ..domain.consent import ConsentLedger, detect_revocation
from ..domain.guardrails import audit_turn
from ..domain.model import AgentConfig
from ..domain.store import VariableStore


def reaudit(config: AgentConfig, turns: List[Dict[str, Any]], state: str = "") -> Dict[str, Any]:
    store, ledger = VariableStore(), ConsentLedger()
    for k, v in config.raw.get("precall_variables", {}).items():
        store.set(k, v, source="constant")
    customer_texts: List[str] = []
    agent_texts: List[str] = []
    rows, agent_turns = [], 0
    for t in turns:
        text = t.get("text", "")
        if t.get("role") == "customer":
            customer_texts.append(text)
            if detect_revocation(text):
                ledger.revoke_all(text)
            continue
        viol = []
        for f in t.get("functions", []) or []:
            name, args, result = f.get("name", ""), f.get("args") or {}, f.get("result") or {}
            tool = config.tool(name)
            if name == "record_consent":
                last = customer_texts[-1] if customer_texts else ""
                ledger.record(str(args.get("purpose", "")), str(args.get("customer_words", "")), last)
            elif tool is not None and tool.kind != "lookup":
                viol += audit_turn(config, state or _owner(config, name), "", {"name": name, "args": args}, store,
                                   ledger, 1, customer_texts, agent_texts)
            store.update_from_tool({f"{name}.{k}": v for k, v in result.items()})
        viol += audit_turn(config, state or config.initial_state, text, None, store, ledger, agent_turns,
                           customer_texts, agent_texts)
        rows.append({"turn": agent_turns, "text": text, "violations": [v.to_dict() for v in viol]})
        agent_texts.append(text)
        agent_turns += 1
    total = sum(len(r["violations"]) for r in rows)
    return {"agent_turns": agent_turns, "violations": total,
            "turns_with_violation": sum(1 for r in rows if r["violations"]), "turns": rows}


def _owner(config: AgentConfig, action: str) -> str:
    """For transcripts without node info: audit the action in the first node that allows it."""
    for s in config.states:
        if action in s.allowed_actions:
            return s.name
    return config.initial_state
