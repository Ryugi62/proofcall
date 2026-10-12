"""UC-1 agent turn: one model call (+ up to two lookup hops), then render, audit, and (guarded) block."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..domain.consent import ConsentLedger, detect_revocation
from ..domain.guardrails import audit_turn, render_slots
from ..domain.model import AgentConfig, Violation
from ..domain.store import VariableStore
from .ports import Clock, LanguageModel, ToolBackend

MAX_LOOKUP_HOPS = 2


class _NoTool:
    kind = "unknown"


_NOTOOL = _NoTool()


@dataclass
class TurnResult:
    spoken: str
    state: str
    action: Optional[Dict[str, Any]]
    intent: str
    events: List[Dict[str, Any]] = field(default_factory=list)
    violations: List[Violation] = field(default_factory=list)      # violations in what was SPOKEN
    blocked: List[Violation] = field(default_factory=list)          # violations caught before speaking (guarded)
    model_ms: float = 0.0
    audit_ms: float = 0.0
    ended: bool = False


def parse_model_json(text: str) -> Dict[str, Any]:
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {"say": "", "intent": "parse_error", "action": None, "next_state": None}


def build_system_prompt(config: AgentConfig, state: str, mode: str) -> str:
    st = config.state(state)
    lines = [f"You are {config.persona}, a voice calling agent for {config.company.get('name', 'the company')}.",
             config.company.get("context", ""), "",
             "GLOBAL RULES (numbered; they never contradict each other):"]
    lines += [f"G{i + 1}. {r}" for i, r in enumerate(config.global_rules)]
    if mode == "guarded":
        lines += ["G0. Never write any digit, amount, percentage, date or time yourself. Write a slot like "
                  "{{price.2bhk.from}} and the system fills it from the tool result. If the value is not yet "
                  "fetched, call the lookup tool first."]
    lines += ["", f"CURRENT STATE: {st.name} — goal: {st.goal}", f"STATE INSTRUCTIONS: {st.instructions}",
              f"ALLOWED ACTIONS IN THIS STATE: {', '.join(st.allowed_actions) or 'none'}",
              "STATES: " + "; ".join(f"{s.name} ({s.goal})" for s in config.states), "",
              "TOOLS:"]
    for t in config.tools:
        sets = f" -> sets {', '.join(t.sets)}" if t.sets else ""
        lines.append(f"- {t.name}({', '.join(f'{k}: {v}' for k, v in t.params.items())}) [{t.kind}] {t.description}{sets}")
    lines += ["", "INTENTS: " + ", ".join(i.name for i in config.intents), "",
              "Reply ONLY with JSON: {\"intent\": <intent>, \"actions\": [{\"name\": <tool>, \"args\": {...}}, ...] (0-3, executed in order, e.g. record_consent then book_site_visit), "
              "\"say\": <what you say next, max 25 words, spoken style, Hinglish if the customer uses Hindi>, "
              "\"next_state\": <state name>}.",
              "If you call a lookup tool, you will get its result and be asked again before speaking."]
    return "\n".join(l for l in lines if l is not None)


class AgentEngine:
    def __init__(self, config: AgentConfig, llm: LanguageModel, tools: ToolBackend, clock: Clock, mode: str = "guarded"):
        assert mode in ("guarded", "baseline")
        self.config, self.llm, self.tools, self.clock, self.mode = config, llm, tools, clock, mode

    def _reachable(self, state: str, proposed: Any) -> str:
        names = {s.name for s in self.config.states}
        if not proposed or proposed not in names:
            return state
        st = self.config.state(state)
        if proposed == state or not st.transitions or proposed in st.transitions.values() \
                or self.config.raw.get("free_transitions", True):
            return proposed
        return state

    def _duplicate(self, action: Optional[Dict[str, Any]], store: VariableStore) -> List[Violation]:
        if not action:
            return []
        marker = self.config.raw.get("once_actions", {}).get(action["name"])
        if marker and store.has(marker):
            return [Violation("DUPLICATE_ACTION", f"{action['name']} already done ({marker}={store.get(marker)})")]
        return []

    def _execute(self, action: Dict[str, Any], store: VariableStore, ledger: ConsentLedger, last_customer: str,
                 events: List[Dict[str, Any]]) -> bool:
        name, args = action["name"], action.get("args") or {}
        if name == "record_consent":
            ok = ledger.record(str(args.get("purpose", "")), str(args.get("customer_words", "")), last_customer)
            events.append({"type": "consent_recorded" if ok else "consent_rejected", "args": args})
            return False
        result = self.tools.call(name, args)
        store.update_from_tool({k: v for k, v in result.items() if k != "message"})
        if name in self.config.raw.get("once_actions", {}) and "message" in result and len(result) == 1:
            events.append({"type": "action_failed", "tool": name, "args": args, "result": result})
            return False
        events.append({"type": "action", "tool": name, "args": args, "result": result})
        return name in ("end_call", "transfer_to_sales")

    def _messages(self, history: List[Dict[str, str]], store: VariableStore, ledger: ConsentLedger,
                  notes: List[str]) -> List[Dict[str, str]]:
        transcript = "\n".join(f"{h['role'].upper()}: {h['text']}" for h in history) or "(call just connected)"
        facts = json.dumps(store.snapshot(), ensure_ascii=False)
        consent = json.dumps(ledger.snapshot(), ensure_ascii=False)
        body = f"TRANSCRIPT:\n{transcript}\n\nVARIABLES (value + source): {facts}\nCONSENT LEDGER: {consent}"
        if notes:
            body += "\n\nSYSTEM NOTES:\n" + "\n".join(notes)
        return [{"role": "user", "content": body}]

    def _actions(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        acts = data.get("actions")
        if not isinstance(acts, list):
            acts = [data.get("action")] if data.get("action") else []
        return [a for a in acts if isinstance(a, dict) and a.get("name")][:3]

    def turn(self, history: List[Dict[str, str]], state: str, store: VariableStore, ledger: ConsentLedger,
             turn_index: int) -> TurnResult:
        events: List[Dict[str, Any]] = []
        notes: List[str] = []
        last_customer = next((h["text"] for h in reversed(history) if h["role"] == "customer"), "")
        if last_customer and detect_revocation(last_customer):
            revoked = ledger.revoke_all(last_customer)
            if revoked:
                events.append({"type": "consent_revoked", "purposes": revoked, "quote": last_customer})
                notes.append(f"Customer revoked consent for: {', '.join(revoked)}. Do not proceed with those actions.")

        model_ms = 0.0
        data: Dict[str, Any] = {}
        for hop in range(MAX_LOOKUP_HOPS + 1):
            t0 = self.clock.now()
            raw = self.llm.complete(build_system_prompt(self.config, state, self.mode),
                                    self._messages(history, store, ledger, notes))
            measured = getattr(self.llm, "last_ms", None)
            model_ms += measured if measured is not None else (self.clock.now() - t0) * 1000
            data = parse_model_json(raw)
            lookups = [a for a in self._actions(data) if (self.config.tool(a["name"]) or _NOTOOL).kind == "lookup"]
            if not lookups or hop >= MAX_LOOKUP_HOPS:
                break
            target = self._reachable(state, data.get("next_state"))
            for a in lookups:
                allowed_here = a["name"] in self.config.state(state).allowed_actions
                allowed_there = a["name"] in self.config.state(target).allowed_actions
                if not allowed_here and allowed_there:
                    events.append({"type": "transition", "from": state, "to": target, "intent": data.get("intent")})
                    state = target
                    allowed_here = True
                if not allowed_here and self.mode == "guarded":
                    notes.append(f"Tool {a['name']} is not allowed in state {state}.")
                    events.append({"type": "lookup_refused", "tool": a["name"], "state": state})
                    continue
                result = self.tools.call(a["name"], a.get("args") or {})
                store.update_from_tool({k: v for k, v in result.items() if k != "message"})
                events.append({"type": "tool", "tool": a["name"], "args": a.get("args") or {}, "result": result})
                notes.append(f"Result of {a['name']}: {json.dumps(result, ensure_ascii=False)}")

        acts = [a for a in self._actions(data) if (self.config.tool(a["name"]) or _NOTOOL).kind != "lookup"]
        next_state = self._reachable(state, data.get("next_state"))
        if next_state != state and all(a["name"] in self.config.state(next_state).allowed_actions for a in acts):
            events.append({"type": "transition", "from": state, "to": next_state, "intent": data.get("intent")})
            state = next_state      # the turn is spoken from the state the conversation moved into
        say = str(data.get("say") or "")

        t1 = self.clock.now()
        customer_texts = [h["text"] for h in history if h["role"] == "customer"]
        ended = False
        action_v: List[Violation] = []
        done: List[Dict[str, Any]] = []
        for a in acts:          # sequential: record_consent then book_site_visit in one turn is allowed
            v = audit_turn(self.config, state, "", a, store, ledger, 1, customer_texts) + self._duplicate(a, store)
            action_v += v
            if self.mode == "baseline" or not v:
                ended = self._execute(a, store, ledger, last_customer, events) or ended
                done.append(a)
        rendered, missing = render_slots(say, store)
        found = audit_turn(self.config, state, rendered, None, store, ledger, turn_index, customer_texts)
        found += [Violation("SLOT_UNFILLED", f"slot {m} has no value") for m in missing]
        found = action_v + found

        blocked: List[Violation] = []
        spoken = rendered
        final_action = done[-1] if done else None
        if self.mode == "guarded" and found:
            blocked = found
            spoken = self.config.state(state).fallback or "Let me check that and get back to you."
            done_line = self.config.raw.get("action_done_lines", {}).get(final_action["name"]) if final_action else None
            if done_line:
                spoken = done_line
            if turn_index == 0 and self.config.raw.get("opening_line"):
                spoken = self.config.raw["opening_line"]
            spoken, _ = render_slots(spoken, store)
            events.append({"type": "blocked", "draft": rendered, "actions": acts,
                           "violations": [v.to_dict() for v in found]})
            found = audit_turn(self.config, state, spoken, None, store, ledger, turn_index, customer_texts)
        audit_ms = (self.clock.now() - t1) * 1000
        return TurnResult(spoken=spoken, state=state, action=final_action, intent=str(data.get("intent", "")),
                          events=events, violations=found, blocked=blocked, model_ms=model_ms, audit_ms=audit_ms,
                          ended=ended)
