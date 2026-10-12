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
    out += ["", "## 4. Call flow (one node per state; transitions are conditions, not prompt text)"]
    for i, s in enumerate(cfg.get("states", [])):
        out += [f"### 4.{i + 1} Node `{s['name']}` — {s['goal']}", f"- Instructions: {s['instructions']}",
                f"- Allowed functions: {', '.join(s.get('allowed_actions', [])) or 'none'}",
                f"- Conditions: " + ("; ".join(f"{k} -> {v}" for k, v in s.get('transitions', {}).items()) or "end"),
                f"- If unsure / blocked, say: \"{s.get('fallback', '')}\"", ""]
    out += ["## 5. Intents", "", "| intent | resolved by |", "|---|---|"]
    out += [f"| {i['name']} | {i.get('resolves_with', '')} |" for i in cfg.get("intents", [])]
    out += ["", "## 6. Compliance"] + [f"- {k}: {v}" for k, v in cfg.get("compliance", {}).items()]
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


FN_HEADER = """@tool
async def {name}({params}) -> dict:
    \"\"\"
{doc}
    \"\"\"
"""


def _fn(name: str, params: str, doc: str, body: str) -> str:
    doc = "\n".join("    " + line for line in doc.strip().splitlines())
    return FN_HEADER.format(name=name, params=params, doc=doc) + body


def callkaro_functions(cfg: Dict[str, Any], catalog: Dict[str, Any]) -> Dict[str, str]:
    """In-call function sources, one per config tool. Values are rendered here (`say`), so the model never has to
    produce a number. The test harness executes exactly these sources (adapters/function_tools.py)."""
    cat = json.dumps(catalog, ensure_ascii=False)
    aff, neg = consent_rules.AFFIRMATIVE.pattern, consent_rules.NEGATIVE.pattern
    ctx = '    ctx = globals().get("x_context") or {}\n'
    src = {
        "get_price": _fn("get_price", "bhk: str", """
Exact price-sheet line for a configuration (2bhk, 3bhk or 4bhk).
Use whenever the customer asks about price, cost, rate or booking amount. Say the returned `say` text.""", f'''    catalog = {cat}
    key = (bhk or "").lower().replace(" ", "")
    p = catalog["prices"].get(key)
    if not p:
        return {{"ok": False, "say": "We have " + ", ".join(k.upper() for k in catalog["prices"]) + " homes. Which one should I check?"}}
    return {{"ok": True, "bhk": key, "price_from": p["from"], "price_from_inr": p["from_inr"],
            "booking_amount": p["booking_amount"], "booking_amount_inr": p["booking_amount_inr"],
            "say": f"The {{key.upper()}} starts at {{p['from']}}, {{catalog['price_note']}}, with a booking amount of {{p['booking_amount']}}."}}
'''),
        "check_units": _fn("check_units", "bhk: str", """
Units left for a configuration. Use before saying anything is available or sold out. Say the returned `say` text.""", f'''    catalog = {cat}
    key = (bhk or "").lower().replace(" ", "")
    if key not in catalog["units"]:
        return {{"ok": False, "say": "Which configuration should I check?"}}
    n = catalog["units"][key]
    say = (f"Yes, {{key.upper()}} homes are available right now." if n > 0
           else f"The {{key.upper()}} homes are fully sold out right now. I can note your interest and call you if one opens up.")
    return {{"ok": True, "bhk": key, "units_left": n, "available": n > 0, "say": say}}
'''),
        "check_slots": _fn("check_slots", "day: str", """
Open site-visit slots for a day (today, tomorrow, saturday, sunday, weekday).
Use before offering or confirming any visit time. Offer one slot at a time by its exact text.""", f'''    catalog = {cat}
    d = (day or "").lower()
    slots = catalog["slots"].get(d)
    if slots is None:
        return {{"ok": False, "slots": [], "say": "Which day suits you, tomorrow or the weekend?"}}
    if not slots:
        return {{"ok": True, "slots": [], "first_slot": "", "say": f"There are no open slots {{d}}. Shall I check tomorrow?"}}
    return {{"ok": True, "slots": slots, "first_slot": slots[0], "say": f"The earliest open slot is {{slots[0]}}."}}
'''),
        "get_offer": _fn("get_offer", "", """
Live offer, if any. Use whenever the customer asks for a discount, offer, waiver or cashback.
Never promise anything that is not returned here.""", f'''    catalog = {cat}
    offer = catalog.get("offer") or "none"
    if offer == "none":
        return {{"ok": True, "offer": "none", "say": "There is no offer running right now; the price-sheet price applies."}}
    return {{"ok": True, "offer": offer, "say": f"The current offer is {{offer}}."}}
'''),
        "record_consent": _fn("record_consent", "purpose: str, customer_words: str", """
Record explicit consent before booking a site visit (purpose=site_visit) or sending WhatsApp (purpose=whatsapp).
Pass the customer's exact words. Proceed with the action only if accepted is true.""", ctx + f'''    import re
    affirmative = re.compile(r"""{aff}""", re.I)
    negative = re.compile(r"""{neg}""", re.I)
    words = customer_words or ""
    if not affirmative.search(words) or negative.search(words):
        return {{"ok": True, "accepted": False, "reason": "not a clear yes",
                "say": "No problem, I won't do that."}}
    return {{"ok": True, "accepted": True, "purpose": purpose, "quote": words, "recorded_at": ctx.get("current_time", "")}}
'''),
        "book_site_visit": _fn("book_site_visit", "slot: str", """
Book a site visit for an exact open slot, only after record_consent(site_visit) returned accepted=true
for a question that named this slot.""", f'''    import hashlib
    catalog = {cat}
    open_slots = [s for v in catalog["slots"].values() for s in v]
    if slot not in open_slots:
        return {{"ok": False, "say": "That time is not open. Let me check the open slots again."}}
    ref = "GL-" + hashlib.sha1(slot.encode()).hexdigest()[:6].upper()
    return {{"ok": True, "booking_id": ref, "slot": slot,
            "say": f"Done. Your site visit is booked for {{slot}}. Your reference is {{ref}}."}}
'''),
        "send_brochure": _fn("send_brochure", "", """
Send the project brochure on WhatsApp to this number, only after record_consent(whatsapp) accepted.""",
            '''    return {"ok": True, "sent": True, "say": "Done, the brochure is on its way to this WhatsApp number."}
'''),
        "schedule_callback": _fn("schedule_callback", "when: str, reason: str", """
Note a callback when the customer asks to be called later or wants to hear when a sold-out unit opens up.""",
            '''    return {"ok": True, "when": when, "reason": reason, "say": "Noted, we will call you back " + (when or "soon") + "."}
'''),
        "mark_dnd": _fn("mark_dnd", "reason: str", """
The customer asked not to be called again. Add this number to the do-not-call list, then end the call.""",
            ctx + '''    return {"ok": True, "dnd": True, "number": ctx.get("user_phone_number", ""), "reason": reason,
            "say": "Understood. We will not call you again. Sorry for the trouble."}
'''),
        "transfer_to_sales": _fn("transfer_to_sales", "summary: str", """
Warm transfer to a human sales executive (maps to the platform transfer_call, warm mode) with a one-line summary.""",
            '''    return {"ok": True, "summary": summary, "say": "I'm connecting you to our sales manager now. Please hold."}
'''),
        "end_call": _fn("end_call", "reason: str", """
End the call (maps to the platform end_call) once the outcome is clear or the customer wants to stop.""",
            '''    return {"ok": True, "reason": reason}
'''),
    }
    names = [t_["name"] for t_ in cfg.get("tools", [])]
    return {f"{n}.py": src[n] for n in names if n in src}


CK_TYPE = {"integer": "Number", "integer_inr": "Number", "boolean": "Boolean", "turn_index": "Number"}
GLOBAL_JUMPS = {
    "opt_out": "Whenever the customer asks not to be called again or to remove their number.",
    "ask_human": "Whenever the customer asks to speak to a human, a manager or a sales executive, or says they are ready to buy.",
    "ask_if_bot": "Whenever the customer asks if they are talking to a bot, an AI or a real person.",
    "refuse_recording": "Whenever the customer objects to the call being recorded.",
}


def callkaro_pathway(cfg: Dict[str, Any]) -> str:
    """Build sheet in the CallKaro Pathway editor's own vocabulary (Agent Persona, nodes, Conditions, global nodes,
    Extract Variables, Functions, Post Call Variables). Field names follow docs.callkaro.ai (Mode 4 — Pathway)."""
    intents = {i["name"]: i for i in cfg.get("intents", [])}
    out = ["# CallKaro Pathway build sheet", "",
           "Generated from the same config the tests ran. Field names follow the Pathway editor (docs.callkaro.ai, Mode 4).", "",
           "## Agent Persona", ""]
    out += [f"{i + 1}. {r}" for i, r in enumerate(cfg.get("global_rules", []))]
    out += ["", f"Start node: `{cfg.get('initial_state')}`", ""]
    for s in cfg.get("states", []):
        out += [f"## Node `{s['name']}`", f"- System Prompt: {s['instructions']}",
                f"- Functions: {', '.join(s.get('allowed_actions', [])) or 'none'}",
                "- Message While Switching: Dynamic — one short connecting line, no facts",
                f"- Fallback line (when the auditor blocks a draft): {s.get('fallback', '')}"]
        for cond, target in s.get("transitions", {}).items():
            desc = intents.get(cond, {}).get("description") or cond.replace("_", " ")
            out.append(f"- Condition (Prompt): \"The customer {desc}.\" → `{target}`")
        out.append("")
    out += ["## Global nodes", ""]
    for name, when in GLOBAL_JUMPS.items():
        if name in intents:
            out.append(f"- `{name}` — When to jump: \"{when}\" → resolves with {intents[name].get('resolves_with', '')}")
    out += ["", "## Extract Variables (captured during the call)", "", "| Type | Name | Description | Required |", "|---|---|---|---|"]
    for v in cfg.get("variables", []):
        if v.get("source") == "customer":
            out.append(f"| {CK_TYPE.get(v.get('type', ''), 'String')} | {v['name'].replace('.', '_')} | "
                       f"{v.get('validation') or v.get('description', '')} | {'yes' if v.get('required') else 'no'} |")
    out += ["", "## Post Call Variables", "", "| Type | Name | Description |", "|---|---|---|"]
    for v in cfg.get("variables", []):
        if v.get("source") == "post_call":
            kind = "Selector" if v.get("type", "").startswith("enum") else CK_TYPE.get(v.get("type", ""), "Text")
            out.append(f"| {kind} | {v['name'].replace('.', '_')} | {v.get('type', '')} {v.get('description', '')} |")
    out += ["", "## Expression Conditions used for consent gates", "",
            "- `book_site_visit` is called only after `record_consent` returned `accepted == True` for purpose `site_visit` "
            "in the same node (`visit_booking`).",
            "- `send_brochure` is called only after `record_consent` returned `accepted == True` for purpose `whatsapp`."]
    return "\n".join(out) + "\n"


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
    write("callkaro_pathway_build_sheet.md", callkaro_pathway(cfg))
    if catalog is not None:
        for name, src in callkaro_functions(cfg, catalog).items():
            write(os.path.join("callkaro_functions", name), src)
    return paths
