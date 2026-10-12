"""AC-13 export completeness + contract test: generated in-call functions behave like the domain rules."""
import asyncio
import json
import os

from proofcall.adapters.export import callkaro_functions, export_all
from proofcall.domain.consent import is_affirmative

ROOT = os.path.dirname(os.path.dirname(__file__))
CFG = json.load(open(os.path.join(ROOT, "configs/rehearsal_realestate.json"), encoding="utf-8"))
CAT = json.load(open(os.path.join(ROOT, "configs/rehearsal_catalog.json"), encoding="utf-8"))


def _load(src, name):
    ns = {"tool": lambda f: f, "x_context": {"current_time": "2026-10-13T10:00:00+05:30"}}
    exec(compile(src, name, "exec"), ns)
    return ns[name[:-3]]


def test_ac13_export_contains_every_part(tmp_path):
    paths = export_all(CFG, str(tmp_path), CAT)
    names = {os.path.relpath(p, tmp_path) for p in paths}
    assert {"agent_config.json", "prompt.md", "variables.md", "pathway.md", "callkaro_pathway_build_sheet.md"} <= names
    sheet = open(tmp_path / "callkaro_pathway_build_sheet.md", encoding="utf-8").read()
    assert "## Agent Persona" in sheet and "When to jump" in sheet and "## Post Call Variables" in sheet
    prompt = open(tmp_path / "prompt.md", encoding="utf-8").read()
    for s in CFG["states"]:
        assert f"Node `{s['name']}`" in prompt
    variables = open(tmp_path / "variables.md", encoding="utf-8").read()
    assert "`get_price.price_from_inr` | integer_inr | tool" in variables
    assert "## 5. Intents" in prompt


def test_generated_get_price_renders_catalog_values():
    f = _load(callkaro_functions(CFG, CAT)["get_price.py"], "get_price.py")
    r = asyncio.get_event_loop().run_until_complete(f("2BHK"))
    assert r["say"] == "The 2BHK starts at ₹1.12 crore, excluding GST and stamp duty, with a booking amount of ₹5 lakh."


def test_generated_record_consent_matches_domain():
    f = _load(callkaro_functions(CFG, CAT)["record_consent.py"], "record_consent.py")
    for words in ["Haan ji, kar dijiye", "yes please book it", "no, don't book", "hmm maybe", "ok whatever... actually no"]:
        r = asyncio.get_event_loop().run_until_complete(f("site_visit", words, "Shall I book Saturday 10:30 AM?"))
        assert r["accepted"] == is_affirmative(words), words


def test_every_generated_function_is_a_config_tool():
    names = {t["name"] for t in CFG["tools"]}
    for fname in callkaro_functions(CFG, CAT):
        assert fname[:-3] in names, fname


def test_function_tools_execute_exported_sources():
    from proofcall.adapters.function_tools import FunctionTools
    ft = FunctionTools(CFG, CAT)
    r = ft.call("check_units", {"bhk": "4BHK"})
    assert r["check_units.available"] is False and "sold out" in r["check_units.say"]
    c = ft.call("record_consent", {"purpose": "site_visit", "customer_words": "Yes, book it", "question_asked": "q"})
    cid = c["record_consent.consent_id"]
    r = ft.call("book_site_visit", {"slot": "Saturday 10:30 AM", "consent_id": "", "consent_quote": "Yes, book it"})
    assert r["book_site_visit.ok"] is False and r["book_site_visit.reason"] == "no valid consent"
    r = ft.call("book_site_visit", {"slot": "Saturday morning", "consent_id": cid, "consent_quote": "Yes, book it"})
    assert r["book_site_visit.ok"] is False and "book_site_visit.booking_id" not in r
    r = ft.call("book_site_visit", {"slot": "Saturday 10:30 AM", "consent_id": cid, "consent_quote": "Yes, book it"})
    assert r["book_site_visit.booking_id"].startswith("GL-") and r["book_site_visit.slot_iso"].startswith("2026-10-17")
    wa = ft.call("send_brochure", {"consent_id": cid, "consent_quote": "Yes, book it"})
    assert wa["send_brochure.ok"] is False          # a site-visit consent cannot be reused for WhatsApp
    assert "sold out" in ft.call("check_units", {"bhk": "4bhk"})["message"]
    assert "sold out" in ft.call("check_units", {"bhk": "4bhk", "lang": "hi"})["message"]
    assert set(ft.sources) == {t["name"] + ".py" for t in CFG["tools"]}
