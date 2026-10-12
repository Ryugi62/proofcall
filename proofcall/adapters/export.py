"""UC-4 export: the same config the runner used -> platform-neutral JSON, numbered prompt, variable table,
pathway diagram, and CallKaro-style in-call Python functions (@tool, async def, imports inside, return dict).
The consent rules in the generated functions are copied from proofcall.domain.consent (single source)."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from ..domain import consent as consent_rules


def _numbered_prompt(cfg: Dict[str, Any]) -> str:
    c = cfg.get("company", {})
    out = [f"# {cfg['name']} — prompt (v{cfg.get('version', '0')})", "",
           "## 1. Role", f"1.1 You are {cfg.get('persona')}, an AI calling assistant for {c.get('name')}.", "",
           "## 2. Goal", f"2.1 {c.get('context', '')}", "",
           "## 3. Guardrails (numbered, non-contradicting)"]
    out += [f"3.{i + 1} {r}" for i, r in enumerate(cfg.get("global_rules", []))]
    out += ["3.0 Prices, availability and offers are spoken only as the exact `say` text returned by get_price / "
            "check_slots / check_units / get_offer. Never compute or round a number in the prompt.", "",
            "## 4. Call flow (one node per state; transitions are conditions, not prompt text)"]
    for i, s in enumerate(cfg.get("states", [])):
        out += [f"### 4.{i + 1} Node `{s['name']}` — {s['goal']}", f"- Instructions: {s['instructions']}",
                f"- Allowed functions: {', '.join(s.get('allowed_actions', [])) or 'none'}",
                f"- Conditions: " + ("; ".join(f"{k} -> {v}" for k, v in s.get('transitions', {}).items()) or "end"),
                f"- If unsure / blocked, say: \"{s.get('fallback', '')}\"", ""]
    return "\n".join(out) + "\n"


def _variables_md(cfg: Dict[str, Any]) -> str:
    rows = ["| variable | type | source | required | validation / meaning |", "|---|---|---|---|---|"]
    for v in cfg.get("variables", []):
        rows.append(f"| `{v['name']}` | {v.get('type', '')} | {v.get('source', '')} | {'yes' if v.get('required') else ''} | "
                    f"{v.get('validation') or v.get('description', '')} |")
    return "# Variables\n\nSource `tool` = may only be filled by a function result. Source `customer` = captured from " \
           "the customer's words. `post_call` = extracted after the call.\n\n" + "\n".join(rows) + "\n"


def _pathway_mermaid(cfg: Dict[str, Any]) -> str:
    lines = ["```mermaid", "flowchart LR"]
    for s in cfg.get("states", []):
        for cond, target in s.get("transitions", {}).items():
            lines.append(f"  {s['name']} -- {cond} --> {target}")
    lines.append("```")
    return "# Pathway\n\n" + "\n".join(lines) + "\n"


def callkaro_functions(cfg: Dict[str, Any], catalog: Dict[str, Any]) -> Dict[str, str]:
    """In-call function sources. Values are rendered here, so the model never has to produce a number."""
    cat = json.dumps(catalog, ensure_ascii=False)
    aff, neg = consent_rules.AFFIRMATIVE.pattern, consent_rules.NEGATIVE.pattern
    return {
        "get_price.py": f'''@tool
async def get_price(bhk: str) -> dict:
    """
    Get the exact price sheet line for a configuration (2bhk, 3bhk or 4bhk).
    Use whenever the customer asks about price, cost, rate or booking amount. Say the returned `say` text exactly.
    """
    catalog = {cat}
    key = (bhk or "").lower().replace(" ", "")
    p = catalog["prices"].get(key)
    if not p:
        return {{"say": "We have 2, 3 and 4 BHK homes. Which one should I check?", "found": False}}
    return {{"say": f"The {{key.upper()}} starts at {{p['from']}}, with a booking amount of {{p['booking_amount']}}.",
            "found": True, "price_from": p["from"], "booking_amount": p["booking_amount"], "source": "price_sheet"}}
''',
        "check_units.py": f'''@tool
async def check_units(bhk: str) -> dict:
    """
    Check how many units are left for a configuration. Use before saying anything is available or sold out.
    Say the returned `say` text exactly.
    """
    catalog = {cat}
    key = (bhk or "").lower().replace(" ", "")
    if key not in catalog["units"]:
        return {{"say": "Which configuration should I check, 2, 3 or 4 BHK?", "found": False}}
    n = catalog["units"][key]
    say = (f"Yes, {{key.upper()}} homes are available right now." if n > 0
           else f"The {{key.upper()}} homes are fully sold out at the moment.")
    return {{"say": say, "units_left": n, "found": True}}
''',
        "check_slots.py": f'''@tool
async def check_slots(day: str) -> dict:
    """
    Get open site-visit slots for a day (today, tomorrow, saturday, sunday, weekday).
    Use before offering or confirming any visit time. Say the returned `say` text exactly.
    """
    catalog = {cat}
    slots = catalog["slots"].get((day or "").lower())
    if slots is None:
        return {{"say": "Which day suits you, tomorrow or the weekend?", "slots": []}}
    if not slots:
        return {{"say": f"There are no open slots {{day}}. Shall I check another day?", "slots": []}}
    return {{"say": "Open slots: " + ", ".join(slots) + ". Which one works?", "slots": slots}}
''',
        "get_offer.py": f'''@tool
async def get_offer() -> dict:
    """
    Get the live offer, if any. Use whenever the customer asks for a discount, offer, waiver or cashback.
    Say the returned `say` text exactly. Never promise anything that is not returned here.
    """
    catalog = {cat}
    offer = catalog.get("offer", "none")
    if not offer or offer == "none":
        return {{"say": "There is no offer running right now; the price sheet price applies.", "offer": "none"}}
    return {{"say": f"The current offer is: {{offer}}.", "offer": offer}}
''',
        "record_consent.py": f'''@tool
async def record_consent(purpose: str, customer_words: str) -> dict:
    """
    Record explicit consent before booking a site visit (purpose=site_visit) or sending WhatsApp (purpose=whatsapp).
    Pass the customer's exact words. Only proceed with the action if accepted is true.
    """
    import re
    affirmative = re.compile(r"""{aff}""", re.I)
    negative = re.compile(r"""{neg}""", re.I)
    words = customer_words or ""
    if not affirmative.search(words) or negative.search(words):
        return {{"accepted": False, "say": "No problem, I won't do that. Is there anything else?",
                "reason": "not a clear yes"}}
    return {{"accepted": True, "purpose": purpose, "quote": words, "recorded_at": x_context.get("current_time", "")}}
''',
    }


def export_all(cfg: Dict[str, Any], out_dir: str, catalog: Dict[str, Any] = None) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    fn_dir = os.path.join(out_dir, "callkaro_functions")
    os.makedirs(fn_dir, exist_ok=True)
    paths = []

    def write(name: str, text: str) -> None:
        p = os.path.join(out_dir, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        paths.append(p)

    write("agent_config.json", json.dumps(cfg, ensure_ascii=False, indent=1))
    write("prompt.md", _numbered_prompt(cfg))
    write("variables.md", _variables_md(cfg))
    write("pathway.md", _pathway_mermaid(cfg))
    if catalog is not None:
        for name, src in callkaro_functions(cfg, catalog).items():
            write(os.path.join("callkaro_functions", name), src)
    return paths
