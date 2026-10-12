"""Agent configuration aggregate and value objects. Standard library only."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Variable:
    name: str
    type: str = "string"
    source: str = "tool"          # tool | customer | constant
    required: bool = False
    description: str = ""
    validation: str = ""


@dataclass(frozen=True)
class Tool:
    name: str
    kind: str = "action"          # lookup (returns variables, agent then speaks) | action
    description: str = ""
    params: Dict[str, str] = field(default_factory=dict)
    sets: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class Intent:
    name: str
    description: str = ""
    resolves_with: str = ""       # tool name or state


@dataclass(frozen=True)
class State:
    name: str
    goal: str
    instructions: str
    allowed_actions: List[str] = field(default_factory=list)
    transitions: Dict[str, str] = field(default_factory=dict)
    fallback: str = ""
    fallback_hi: str = ""


@dataclass(frozen=True)
class ClaimRule:
    code: str
    pattern: str
    requires_var_prefix: str
    unless: str = ""          # if this matches the same sentence, it is a question/check/negation, not a claim


@dataclass(frozen=True)
class Violation:
    code: str
    evidence: str

    def to_dict(self) -> Dict[str, str]:
        return {"code": self.code, "evidence": self.evidence}


@dataclass
class AgentConfig:
    name: str
    persona: str
    states: List[State]
    variables: List[Variable] = field(default_factory=list)
    tools: List[Tool] = field(default_factory=list)
    intents: List[Intent] = field(default_factory=list)
    global_rules: List[str] = field(default_factory=list)
    disclosure_required_any: List[str] = field(default_factory=list)
    forbidden_claims: List[str] = field(default_factory=list)
    claim_rules: List[ClaimRule] = field(default_factory=list)
    consent_gated_actions: Dict[str, str] = field(default_factory=dict)
    initial_state: str = ""
    company: Dict[str, Any] = field(default_factory=dict)
    voice: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "AgentConfig":
        states = [State(name=s["name"], goal=s.get("goal", ""), instructions=s.get("instructions", ""),
                        allowed_actions=list(s.get("allowed_actions", [])),
                        transitions=dict(s.get("transitions", {})), fallback=s.get("fallback", ""),
                        fallback_hi=s.get("fallback_hi", ""))
                  for s in d.get("states", [])]
        return AgentConfig(
            name=d["name"], persona=d.get("persona", ""), states=states,
            variables=[Variable(**v) for v in d.get("variables", [])],
            tools=[Tool(name=t["name"], kind=t.get("kind", "action"), description=t.get("description", ""),
                        params=dict(t.get("params", {})), sets=list(t.get("sets", []))) for t in d.get("tools", [])],
            intents=[Intent(**i) for i in d.get("intents", [])],
            global_rules=list(d.get("global_rules", [])),
            disclosure_required_any=list(d.get("disclosure", {}).get("required_any", [])),
            forbidden_claims=list(d.get("forbidden_claims", [])),
            claim_rules=[ClaimRule(**c) for c in d.get("claim_rules", [])],
            consent_gated_actions=dict(d.get("consent_gated_actions", {})),
            initial_state=d.get("initial_state") or (states[0].name if states else ""),
            company=dict(d.get("company", {})), voice=dict(d.get("voice", {})), raw=d,
        )

    def state(self, name: str) -> State:
        for s in self.states:
            if s.name == name:
                return s
        raise KeyError(f"unknown state {name!r}")

    def tool(self, name: str) -> Optional[Tool]:
        for t in self.tools:
            if t.name == name:
                return t
        return None


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    persona: str
    goal: str
    tactics: List[str]
    expected_outcome: str          # booked | declined | handoff | callback
    edge_case: bool = False
    targets: List[str] = field(default_factory=list)   # guardrails attacked
    max_turns: int = 14
    language: str = "en"
    precall: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Scenario":
        return Scenario(id=d["id"], title=d["title"], persona=d["persona"], goal=d["goal"],
                        tactics=list(d.get("tactics", [])), expected_outcome=d["expected_outcome"],
                        edge_case=bool(d.get("edge_case", False)), targets=list(d.get("targets", [])),
                        max_turns=int(d.get("max_turns", 14)), language=d.get("language", "en"),
                        precall=dict(d.get("precall", {})))
