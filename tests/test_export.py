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
    assert {"agent_config.json", "prompt.md", "variables.md", "pathway.md"} <= names
    prompt = open(tmp_path / "prompt.md", encoding="utf-8").read()
    for s in CFG["states"]:
        assert f"Node `{s['name']}`" in prompt
    variables = open(tmp_path / "variables.md", encoding="utf-8").read()
    assert "`price.<bhk>.from` | money_inr | tool" in variables


def test_generated_quote_price_renders_catalog_values():
    f = _load(callkaro_functions(CFG, CAT)["quote_price.py"], "quote_price.py")
    r = asyncio.get_event_loop().run_until_complete(f("2BHK"))
    assert r["say"] == "The 2BHK starts at ₹1.12 crore, with a booking amount of ₹5 lakh."


def test_generated_record_consent_matches_domain():
    f = _load(callkaro_functions(CFG, CAT)["record_consent.py"], "record_consent.py")
    for words in ["Haan ji, kar dijiye", "yes please book it", "no, don't book", "hmm maybe", "ok whatever... actually no"]:
        r = asyncio.get_event_loop().run_until_complete(f("site_visit", words))
        assert r["accepted"] == is_affirmative(words), words
