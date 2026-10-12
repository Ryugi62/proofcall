"""Acceptance tests AC-1 … AC-10 (domain only, no network)."""
from proofcall.domain.model import AgentConfig
from proofcall.domain.store import VariableStore
from proofcall.domain.consent import ConsentLedger, detect_revocation
from proofcall.domain.guardrails import audit_turn, render_slots, extract_numbers

CONFIG = AgentConfig.from_dict({
    "name": "test",
    "repair_once": False,
    "persona": "Asha",
    "disclosure": {"required_any": ["recorded"]},
    "forbidden_claims": [r"\bguarantee(?:d)?\b"],
    "claim_rules": [
        {"code": "AVAILABILITY_UNVERIFIED",
         "pattern": r"\b(?:is|are) (?:available|free|open)\b|\bfully booked\b",
         "requires_var_prefix": "availability."},
        {"code": "BOOKING_UNBACKED",
         "pattern": r"\b(?:i have|i've|is now|has been)\s+(?:booked|confirmed)\b",
         "requires_var_prefix": "booking."},
    ],
    "consent_gated_actions": {"book_slot": "booking"},
    "variables": [],
    "tools": [{"name": "get_price", "kind": "lookup"}, {"name": "book_slot", "kind": "action"},
              {"name": "end_call", "kind": "action"}],
    "intents": [],
    "states": [
        {"name": "pitch", "goal": "g", "instructions": "i", "allowed_actions": ["get_price"],
         "fallback": "Let me get that exactly right for you."},
        {"name": "booking", "goal": "g", "instructions": "i", "allowed_actions": ["book_slot", "end_call"],
         "fallback": "One moment."},
    ],
})


def codes(vs):
    return sorted(v.code for v in vs)


def test_ac1_unsourced_price_is_violation():
    store = VariableStore()
    vs = audit_turn(CONFIG, "pitch", "The plan costs Rs 1,499 per month.", None, store, ConsentLedger(), turn_index=3)
    assert "PRICE_UNSOURCED" in codes(vs)


def test_ac1_number_words_with_currency_are_caught():
    store = VariableStore()
    vs = audit_turn(CONFIG, "pitch", "It is just five thousand rupees.", None, store, ConsentLedger(), turn_index=3)
    assert "PRICE_UNSOURCED" in codes(vs)


def test_ac2_tool_sourced_price_is_fine():
    store = VariableStore()
    store.set("price.basic.monthly", "₹1,499", source="tool")
    vs = audit_turn(CONFIG, "pitch", "The plan costs Rs 1499 per month.", None, store, ConsentLedger(), turn_index=3)
    assert vs == []


def test_ac2_customer_number_echo_is_not_a_price():
    store = VariableStore()
    vs = audit_turn(CONFIG, "pitch", "Got it, a 3 bedroom house.", None, store, ConsentLedger(), turn_index=3,
                    customer_texts=["We have a 3 bedroom house"])
    assert vs == []


def test_ac1_percent_discount_unsourced():
    vs = audit_turn(CONFIG, "pitch", "I can give you 20% off today.", None, VariableStore(), ConsentLedger(), turn_index=3)
    assert "PRICE_UNSOURCED" in codes(vs)


def test_ac3_availability_claim_needs_tool():
    store = VariableStore()
    vs = audit_turn(CONFIG, "pitch", "Tomorrow morning is available.", None, store, ConsentLedger(), turn_index=3)
    assert "AVAILABILITY_UNVERIFIED" in codes(vs)
    store.set("availability.slots", "2026-10-14 10:00", source="tool")
    vs = audit_turn(CONFIG, "pitch", "Tomorrow morning is available.", None, store, ConsentLedger(), turn_index=3)
    assert "AVAILABILITY_UNVERIFIED" not in codes(vs)


def test_booking_claim_needs_booking_var():
    vs = audit_turn(CONFIG, "booking", "Great, I have booked your visit.", None, VariableStore(), ConsentLedger(), turn_index=5)
    assert "BOOKING_UNBACKED" in codes(vs)


def test_ac4_gated_action_without_consent():
    vs = audit_turn(CONFIG, "booking", "Booking now.", {"name": "book_slot", "args": {}}, VariableStore(),
                    ConsentLedger(), turn_index=5)
    assert "ACTION_WITHOUT_CONSENT" in codes(vs)


def test_ac4_gated_action_with_consent():
    ledger = ConsentLedger()
    assert ledger.record("booking", "yes please book it", last_customer_text="Yes please book it for Tuesday")
    vs = audit_turn(CONFIG, "booking", "Booking now.", {"name": "book_slot", "args": {}}, VariableStore(),
                    ledger, turn_index=5)
    assert vs == []


def test_ac5_negative_or_missing_quote_rejected():
    ledger = ConsentLedger()
    assert not ledger.record("booking", "no", last_customer_text="No, don't book anything")
    assert not ledger.record("booking", "nahi", last_customer_text="nahi abhi nahi")
    assert not ledger.record("booking", "yes go ahead", last_customer_text="Tell me the price first")
    assert not ledger.has("booking")


def test_ac6_revocation():
    ledger = ConsentLedger()
    assert ledger.record("booking", "haan ji", last_customer_text="Haan ji, kar dijiye")
    assert detect_revocation("Actually wait, cancel that, I don't want it")
    ledger.revoke_all("Actually wait, cancel that")
    assert not ledger.has("booking")
    vs = audit_turn(CONFIG, "booking", "Booking now.", {"name": "book_slot", "args": {}}, VariableStore(),
                    ledger, turn_index=7)
    assert "ACTION_WITHOUT_CONSENT" in codes(vs)


def test_ac7_forbidden_claim():
    vs = audit_turn(CONFIG, "pitch", "Savings are guaranteed.", None, VariableStore(), ConsentLedger(), turn_index=3)
    assert "FORBIDDEN_CLAIM" in codes(vs)


def test_ac8_disclosure_on_first_turn():
    vs = audit_turn(CONFIG, "pitch", "Hi, this is Asha.", None, VariableStore(), ConsentLedger(), turn_index=0)
    assert "DISCLOSURE_MISSING" in codes(vs)
    vs = audit_turn(CONFIG, "pitch", "Hi, this is Asha, this call is recorded.", None, VariableStore(),
                    ConsentLedger(), turn_index=0)
    assert vs == []


def test_ac9_render_slots():
    store = VariableStore()
    store.set("price.basic.monthly", "₹1,499", source="tool")
    text, missing = render_slots("It is {{price.basic.monthly}} a month, setup {{price.basic.setup}}.", store)
    assert "₹1,499" in text
    assert missing == ["price.basic.setup"]


def test_ac10_action_not_allowed_in_state():
    ledger = ConsentLedger()
    ledger.record("booking", "yes", last_customer_text="yes")
    vs = audit_turn(CONFIG, "pitch", "Booking now.", {"name": "book_slot", "args": {}}, VariableStore(),
                    ledger, turn_index=3)
    assert "ACTION_NOT_ALLOWED" in codes(vs)


def test_extract_numbers_normalises():
    assert extract_numbers("₹1,499 and 10:00 and 09") == ["1499", "10", "0", "9"]


def test_hinglish_number_words_with_currency_are_caught():
    vs = audit_turn(CONFIG, "pitch", "Bas teen sau rupaye mahina.", None, VariableStore(), ConsentLedger(), turn_index=3)
    assert "PRICE_UNSOURCED" in codes(vs)
    vs = audit_turn(CONFIG, "pitch", "Sirf paanch hazaar mein ho jayega.", None, VariableStore(), ConsentLedger(), turn_index=3)
    assert "PRICE_UNSOURCED" in codes(vs)


def test_devanagari_amount_is_caught():
    vs = audit_turn(CONFIG, "pitch", "कीमत ₹१४९९ है", None, VariableStore(), ConsentLedger(), turn_index=3)
    assert "PRICE_UNSOURCED" in codes(vs)
    vs = audit_turn(CONFIG, "pitch", "सिर्फ पाँच सौ रुपये", None, VariableStore(), ConsentLedger(), turn_index=3)
    assert "PRICE_UNSOURCED" in codes(vs)


def test_hindi_amount_matching_tool_value_is_fine():
    store = VariableStore()
    store.set("price.basic.monthly", "₹500", source="tool")
    vs = audit_turn(CONFIG, "pitch", "Sirf paanch sau rupaye.", None, store, ConsentLedger(), turn_index=3)
    assert vs == []


def test_plain_count_words_are_not_amounts():
    vs = audit_turn(CONFIG, "pitch", "Just one moment, I have two options for you.", None, VariableStore(),
                    ConsentLedger(), turn_index=3)
    assert vs == []


def test_english_do_is_not_two():
    store = VariableStore()
    store.set("price.basic.monthly", "₹500", source="tool")
    vs = audit_turn(CONFIG, "pitch", "I can do five hundred rupees for the basic plan.", None, store,
                    ConsentLedger(), turn_index=3)
    assert vs == []
    vs = audit_turn(CONFIG, "pitch", "Do hazaar rupaye lagenge.", None, VariableStore(), ConsentLedger(), turn_index=3)
    assert "PRICE_UNSOURCED" in codes(vs)


def test_crore_in_words_matches_tool_value():
    store = VariableStore()
    store.set("price.2bhk.from", "₹1.12 crore", source="tool")
    ok = audit_turn(CONFIG, "pitch", "It starts at one crore twelve lakh rupees.", None, store, ConsentLedger(), turn_index=3)
    assert ok == []
    bad = audit_turn(CONFIG, "pitch", "It starts at one crore ten lakh.", None, store, ConsentLedger(), turn_index=3)
    assert "PRICE_UNSOURCED" in codes(bad)


def test_consent_phrase_level_negation_and_devanagari():
    from proofcall.domain.consent import is_affirmative, detect_opt_out
    assert not is_affirmative("I'm not sure")
    assert not is_affirmative("not interested, okay")
    assert not is_affirmative("hmm maybe")
    assert is_affirmative("Yes, no problem")
    assert is_affirmative("don't worry, go ahead")
    assert is_affirmative("हाँ, कर दीजिए")
    assert not is_affirmative("नहीं, अभी नहीं")
    assert detect_opt_out("Please don't call me again, remove my number")
    assert not detect_opt_out("Don't book anything yet")


CFG2 = AgentConfig.from_dict(dict(CONFIG.raw, max_questions_per_turn=1, mirror_language=True,
                                  consent_must_name={"book_slot": "slot"}))


def test_multi_question_and_language_mismatch():
    vs = audit_turn(CFG2, "pitch", "What is your budget? And when do you plan to buy?", None, VariableStore(),
                    ConsentLedger(), turn_index=3, customer_texts=["I want a 2BHK"])
    assert "MULTI_QUESTION" in codes(vs)
    vs = audit_turn(CFG2, "pitch", "Aapka budget kya hai?", None, VariableStore(), ConsentLedger(), turn_index=3,
                    customer_texts=["I want a 2BHK"])
    assert "LANGUAGE_MISMATCH" in codes(vs)
    vs = audit_turn(CFG2, "pitch", "Aapka budget kya hai?", None, VariableStore(), ConsentLedger(), turn_index=3,
                    customer_texts=["3BHK ka rate kya hai?"])
    assert vs == []


def test_slot_must_be_named_in_consent_question():
    ledger = ConsentLedger()
    ledger.record("booking", "yes", last_customer_text="yes")
    act = {"name": "book_slot", "args": {"slot": "Saturday 10:30 AM"}}
    vs = audit_turn(CFG2, "booking", "", act, VariableStore(), ledger, 5, agent_texts=["Shall I book Saturday morning?"])
    assert "SLOT_NOT_NAMED" in codes(vs)
    vs = audit_turn(CFG2, "booking", "", act, VariableStore(), ledger, 5,
                    agent_texts=["Shall I book the visit for Saturday 10:30 AM?"])
    assert vs == []
