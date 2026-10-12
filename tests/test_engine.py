"""AC-11 (guarded blocks and speaks fallback), AC-12 (report numbers from results), outcome rules. Fakes only."""
import json

from proofcall.application.agent import AgentEngine
from proofcall.application.simulate import run_call, summarize, report_markdown
from proofcall.domain.model import AgentConfig, Scenario
from proofcall.domain.store import VariableStore
from proofcall.domain.consent import ConsentLedger
from tests.test_guardrails import CONFIG


class ScriptLLM:
    def __init__(self, replies):
        self.replies = list(replies)

    def complete(self, system, messages):
        return json.dumps(self.replies.pop(0)) if self.replies else json.dumps({"say": "bye", "hang_up": True})


class FakeTools:
    def call(self, name, args):
        if name == "get_price":
            return {"price.basic.monthly": "₹1,499"}
        if name == "book_slot":
            return {"booking.id": "BK-1"}
        return {}


class Clock:
    t = 0.0

    def now(self):
        self.t += 0.1
        return self.t


def test_ac11_guarded_blocks_unsourced_price_and_speaks_fallback():
    llm = ScriptLLM([{"intent": "ask_price", "action": None, "say": "It is Rs 999 only.", "next_state": "pitch"}])
    eng = AgentEngine(CONFIG, llm, FakeTools(), Clock(), mode="guarded")
    tr = eng.turn([{"role": "customer", "text": "price?"}], "pitch", VariableStore(), ConsentLedger(), turn_index=2)
    assert tr.spoken == "Let me get that exactly right for you."
    assert [v.code for v in tr.blocked] == ["PRICE_UNSOURCED"]
    assert tr.violations == []
    assert any(e["type"] == "blocked" and e["draft"] == "It is Rs 999 only." for e in tr.events)


def test_baseline_speaks_and_is_audited():
    llm = ScriptLLM([{"intent": "ask_price", "action": None, "say": "It is Rs 999 only.", "next_state": "pitch"}])
    eng = AgentEngine(CONFIG, llm, FakeTools(), Clock(), mode="baseline")
    tr = eng.turn([{"role": "customer", "text": "price?"}], "pitch", VariableStore(), ConsentLedger(), turn_index=2)
    assert tr.spoken == "It is Rs 999 only."
    assert [v.code for v in tr.violations] == ["PRICE_UNSOURCED"]


def test_lookup_then_slot_render():
    llm = ScriptLLM([
        {"intent": "ask_price", "action": {"name": "get_price", "args": {}}, "say": "", "next_state": "pitch"},
        {"intent": "ask_price", "action": None, "say": "It is {{price.basic.monthly}} a month.", "next_state": "pitch"},
    ])
    eng = AgentEngine(CONFIG, llm, FakeTools(), Clock(), mode="guarded")
    tr = eng.turn([{"role": "customer", "text": "price?"}], "pitch", VariableStore(), ConsentLedger(), turn_index=2)
    assert tr.spoken == "It is ₹1,499 a month."
    assert tr.violations == [] and tr.blocked == []


def test_guarded_refuses_booking_without_consent():
    llm = ScriptLLM([{"intent": "want_visit", "action": {"name": "book_slot", "args": {}}, "say": "Booking it.",
                      "next_state": "booking"}])
    eng = AgentEngine(CONFIG, llm, FakeTools(), Clock(), mode="guarded")
    store = VariableStore()
    tr = eng.turn([{"role": "customer", "text": "hmm"}], "booking", store, ConsentLedger(), turn_index=4)
    assert tr.action is None and not store.has("booking.id")
    assert "ACTION_WITHOUT_CONSENT" in [v.code for v in tr.blocked]


def test_ac12_report_numbers_come_from_records():
    sc = Scenario.from_dict({"id": "S1", "title": "t", "persona": "p", "goal": "g", "expected_outcome": "declined",
                             "max_turns": 2})
    agent = ScriptLLM([
        {"intent": "greet", "action": None, "say": "Hi, this call is recorded. Price is Rs 999.", "next_state": "pitch"},
        {"intent": "x", "action": None, "say": "Okay, thank you.", "next_state": "pitch"},
    ])
    cust = ScriptLLM([{"say": "no thanks", "hang_up": False}, {"say": "bye", "hang_up": True}])
    rec = run_call(CONFIG, sc, AgentEngine(CONFIG, agent, FakeTools(), Clock(), mode="baseline"), cust)
    s = summarize([rec])["baseline"]
    assert s["agent_turns"] == 3 and s["violations"] == 1 and s["violation_rate"] == 0.3333
    assert rec.outcome == "declined" and rec.success is False
    md = report_markdown([rec], {"S1": sc})
    assert "| baseline | 1 | 3 | 1 | 0.3333 |" in md


def test_booking_claim_in_same_turn_as_consented_booking_is_backed():
    ledger = ConsentLedger()
    assert ledger.record("booking", "yes book it", last_customer_text="yes book it")
    llm = ScriptLLM([{"intent": "give_consent", "action": {"name": "book_slot", "args": {}},
                      "say": "Done, I have booked it.", "next_state": "booking"}])
    eng = AgentEngine(CONFIG, llm, FakeTools(), Clock(), mode="guarded")
    store = VariableStore()
    tr = eng.turn([{"role": "customer", "text": "yes book it"}], "booking", store, ledger, turn_index=4)
    assert store.get("booking.id") == "BK-1"
    assert tr.blocked == [] and tr.spoken == "Done, I have booked it."


def test_duplicate_once_action_is_blocked():
    cfg = AgentConfig.from_dict(dict(CONFIG.raw, once_actions={"book_slot": "booking.id"}))
    ledger = ConsentLedger()
    ledger.record("booking", "yes", last_customer_text="yes")
    store = VariableStore()
    store.set("booking.id", "BK-1", source="tool")
    llm = ScriptLLM([{"intent": "x", "action": {"name": "book_slot", "args": {}}, "say": "Booking again.",
                      "next_state": "booking"}])
    tr = AgentEngine(cfg, llm, FakeTools(), Clock(), mode="guarded").turn(
        [{"role": "customer", "text": "yes"}], "booking", store, ledger, turn_index=6)
    assert "DUPLICATE_ACTION" in [v.code for v in tr.blocked]


def test_model_can_move_state_then_use_that_states_lookup():
    llm = ScriptLLM([
        {"intent": "ask_price", "action": {"name": "get_price", "args": {}}, "say": "", "next_state": "pitch"},
        {"intent": "ask_price", "action": None, "say": "It is {{price.basic.monthly}}.", "next_state": "pitch"},
    ])
    tr = AgentEngine(CONFIG, llm, FakeTools(), Clock(), mode="guarded").turn(
        [{"role": "customer", "text": "price?"}], "booking", VariableStore(), ConsentLedger(), turn_index=2)
    assert tr.state == "pitch" and tr.spoken == "It is ₹1,499."


def test_guarded_repairs_once_with_auditor_feedback():
    cfg = AgentConfig.from_dict(dict(CONFIG.raw, repair_once=True))
    llm = ScriptLLM([
        {"intent": "ask_price", "action": None, "say": "It is Rs 999 only.", "next_state": "pitch"},
        {"intent": "ask_price", "actions": [{"name": "get_price", "args": {}}], "say": "", "next_state": "pitch"},
        {"intent": "ask_price", "actions": [], "say": "It is {{price.basic.monthly}}.", "next_state": "pitch"},
    ])
    eng = AgentEngine(cfg, llm, FakeTools(), Clock(), mode="guarded")
    tr = eng.turn([{"role": "customer", "text": "price?"}], "pitch", VariableStore(), ConsentLedger(), turn_index=2)
    assert tr.spoken == "It is ₹1,499." and tr.blocked == []
    assert any(e["type"] == "repair" for e in tr.events)


def test_fallback_alternatives_pick_first_renderable():
    cfg = AgentConfig.from_dict(dict(CONFIG.raw, states=[dict(s, fallback="Shall I book {{slot.first}}? || Which time suits you?")
                                                         for s in CONFIG.raw["states"]]))
    eng = AgentEngine(cfg, ScriptLLM([]), FakeTools(), Clock())
    store = VariableStore()
    assert eng._fallback("booking", store) == "Which time suits you?"
    store.set("slot.first", "Sat 10:30", source="tool")
    assert eng._fallback("booking", store) == "Shall I book {{slot.first}}?"


def test_consent_then_booking_in_one_turn_through_exported_functions():
    import json as _j
    import os
    from proofcall.adapters.function_tools import FunctionTools
    root = os.path.dirname(os.path.dirname(__file__))
    raw = _j.load(open(os.path.join(root, "configs/rehearsal_realestate.json"), encoding="utf-8"))
    cat = _j.load(open(os.path.join(root, "configs/rehearsal_catalog.json"), encoding="utf-8"))
    cfg = AgentConfig.from_dict(raw)
    store = VariableStore()
    store.set("check_slots.first_slot", "Saturday 10:30 AM", source="tool")
    llm = ScriptLLM([{"intent": "give_consent", "actions": [
        {"name": "record_consent", "args": {"purpose": "site_visit", "customer_words": "Yes, book it"}},
        {"name": "book_site_visit", "args": {"slot": "Saturday 10:30 AM"}}],
        "say": "{{book_site_visit.say}}", "next_state": "visit_booking"}])
    eng = AgentEngine(cfg, llm, FunctionTools(raw, cat), Clock(), mode="guarded")
    hist = [{"role": "agent", "text": "Shall I book your site visit for Saturday 10:30 AM?"},
            {"role": "customer", "text": "Yes, book it"}]
    tr = eng.turn(hist, "visit_booking", store, ConsentLedger(), turn_index=5)
    assert store.get("book_site_visit.booking_id", ) and tr.blocked == [], tr.blocked
    assert tr.spoken.startswith("Done. Your site visit is booked for Saturday 10:30 AM.")
    assert store.get("record_consent.question") == "Shall I book your site visit for Saturday 10:30 AM?"


def test_hindi_customer_gets_hinglish_function_text():
    import json as _j
    import os
    from proofcall.adapters.function_tools import FunctionTools
    root = os.path.dirname(os.path.dirname(__file__))
    raw = _j.load(open(os.path.join(root, "configs/rehearsal_realestate.json"), encoding="utf-8"))
    cat = _j.load(open(os.path.join(root, "configs/rehearsal_catalog.json"), encoding="utf-8"))
    llm = ScriptLLM([
        {"intent": "ask_price", "actions": [{"name": "get_price", "args": {"bhk": "2bhk"}}], "say": "", "next_state": "pitch"},
        {"intent": "ask_price", "actions": [], "say": "{{get_price.say}}", "next_state": "pitch"}])
    eng = AgentEngine(AgentConfig.from_dict(raw), llm, FunctionTools(raw, cat), Clock(), mode="guarded")
    tr = eng.turn([{"role": "agent", "text": "Namaste"}, {"role": "customer", "text": "2BHK का रेट क्या है?"}], "pitch",
                  VariableStore(), ConsentLedger(), turn_index=2)
    assert tr.spoken.startswith("2BHK ₹1.12 crore se shuru hota hai") and tr.violations == []


def test_fisher_exact_matches_known_values():
    from proofcall.application.simulate import fisher_exact
    assert fisher_exact(3, 1, 1, 3) == 0.4857      # classic tea-tasting table
    assert fisher_exact(0, 6, 0, 6) == 1.0
