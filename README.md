# ProofCall — a call agent that proves its guardrails

**Values are rendered, never generated.** The language model never writes a price, an availability claim or a booking confirmation in its own words. It inserts the function's sentence (`{{get_price.say}}`), and the number comes from that function's result. Consent is stored as the customer's own words. A deterministic auditor (regex and set lookups, no second LLM) checks every agent turn and can block it before it is spoken.

Built for *The Golden Hour — A Voice AI Hackathon* (E-Cell IIT Kharagpur × CallKaro AI), task "Zero to Conversion": an autonomous voice agent bound by guardrails around **pricing, availability and explicit consent**.

> Scope of the numbers below: they come from **text-only simulated calls** (LLM agent ↔ LLM-simulated customer). Model latency here excludes speech-to-text, text-to-speech and telephony. The contest recordings come from the voice platform's own test calls. Both voices in any rehearsal audio are synthetic. No real person is called.

## What is different (compared with existing tools)

| Tool | How it tests or guards a voice agent | What ProofCall adds |
|---|---|---|
| CallKaro Simulation + AI Auditor ([docs](https://docs.callkaro.ai)) | Fake user with success criteria, batch runs. LLM auditor flags callflow, function accuracy and "incorrect promises" | The same calls re-audited by **deterministic rules**: a number counts only if a function returned it. Reports where the two auditors disagree |
| Vapi Test Suites ([docs](https://docs.vapi.ai/test/test-suites)) | An AI tester calls the agent and checks the outcome and guardrails | Guardrails enforced **before speaking** (blocked turn → safe fallback), not only graded afterwards |
| Retell batch testing ([blog](https://www.retellai.com/blog/retell-ai-introduces-simulation-and-batch-testing-for-ai-agents)) | Simulated users (identity, goal, personality) at scale | Hinglish and Devanagari amounts ("teen sau", "पाँच सौ", "one crore twelve lakh") normalised and checked against tool values |
| Bland scenarios ([docs](https://docs.bland.ai/tutorials/scenarios)) | Simulated agent, assertions, repeated runs for flakiness | Consent = verbatim affirmative quote from the **last** customer utterance; revocation ("cancel that") voids it immediately |

## Rubric map

| Criterion | Where to look |
|---|---|
| Architecture & Prompt Engineering | `configs/*.json` states (node per stage, allowed functions, conditions, fallback); `export/prompt.md` numbered non-contradicting rules |
| Data Schema & Variable Design | `export/variables.md`. Every variable has a type and a source (`tool`, `customer`, `constant`, `post_call`). Price, availability and offer values are `tool` only |
| Actions, Tool Calling & Intent Resolution | 17 intents, 12 functions; `export/callkaro_functions/*.py` (`@tool async def`, values rendered inside the function). **The test harness executes these exact function files**, so what was tested is what is exported |
| Testing Rigour & Edge-Case Handling | `scenarios/*.yaml`: 19 self-designed scenarios, 14 edge cases. `runs/*/report.md` compares guarded and prompt-only baseline with the same auditor, with 95% Wilson intervals. The auditor itself is measured: on a 120-case held-out set written by an independent labeller from the rule definitions only, its first untuned run scored 106/120 exact with 2/58 false blocks on clean turns (`eval/auditor_heldout_v2_eval.md`); development sets in `eval/auditor_eval.md` |
| Call Quality, Latency & Naturalness | Replies ≤ 25 words, Hinglish mirroring, latency per turn in every report |

## How it works

```
customer turn ─► agent model (JSON: intent, action, say-with-slots, next_state)
                    │ lookup function? ─► tool result ─► variables(source=tool) ─► ask model again
                    ▼
     action pre-check (allowed in node? consent live? already done?) ─► execute
                    ▼
     render slots from variables ─► deterministic audit ─► violations?
                    │ guarded: speak node fallback / "done" line instead, log the blocked draft
                    │ baseline: speak it, count it
                    ▼
                 spoken turn + audit log
```

Violation codes: `PRICE_UNSOURCED`, `NUMBER_UNSOURCED`, `AVAILABILITY_UNVERIFIED`, `BOOKING_UNBACKED`, `BROCHURE_UNBACKED`, `OFFER_UNVERIFIED`, `FORBIDDEN_CLAIM`, `DISCLOSURE_MISSING`, `MULTI_QUESTION`, `LANGUAGE_MISMATCH`, `SLOT_NOT_NAMED`, `ACTION_NOT_ALLOWED`, `ACTION_WITHOUT_CONSENT`, `DUPLICATE_ACTION`, `SLOT_UNFILLED`.

**Consent is enforced inside the exported functions too**: `record_consent` issues a `consent_id` only for a clear yes, and `book_site_visit` / `send_brochure` return `ok: false` unless that id matches the customer's quote for the right purpose (a site-visit yes cannot be reused for WhatsApp). So the gate holds on the platform even without this harness.

Every function speaks English or Hinglish (`lang`), and the call locks to Hinglish once the customer speaks Hindi.

When a draft is blocked, the agent gets one repair attempt with the auditor's reasons. If the repair is also blocked, it speaks the node's fallback. Fallbacks are slot-aware (`Shall I book your site visit for {{check_slots.first_slot}}?`).

**Violation rate** = guardrail violations in spoken agent turns ÷ agent turns. The same deterministic auditor is used for both modes.

## Results

<!-- RESULTS:BEGIN (generated by scripts/update_readme.py from runs/*/results.json — do not edit by hand) -->
**Run `rehearsal-2026-10-12`** — [report](runs/rehearsal-2026-10-12/report.md)

| mode | calls | agent turns | violations | turns with a violation (95% CI) | blocked before speaking | outcome match | task success (95% CI) | median / p90 model ms | median audit ms |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 6 | 35 | 2 | 2 [0.0158, 0.1861] | 0 | 4/6 | 4/6 [0.3, 0.9032] | 1292 / 3589 | 0.113 |
| guarded | 6 | 33 | 0 | 0 [0.0, 0.1043] | 1 | 6/6 | 6/6 [0.6097, 1.0] | 1283 / 3277 | 0.152 |

Calls with ≥1 violation, baseline vs guarded: Fisher exact p = 1.0 (call level). Task success: p = 0.4545.

<!-- RESULTS:END -->

## Run it

```bash
python3 -m pytest -q                                   # domain + engine + export tests, no network
export GEMINI_API_KEY=...                              # free tier is enough for small runs
python3 -m proofcall run --config configs/rehearsal_realestate.json --catalog configs/rehearsal_catalog.json \
  --scenarios scenarios/rehearsal_realestate.yaml --modes guarded,baseline --runs 1 --out runs/demo
python3 -m proofcall export --config configs/rehearsal_realestate.json --catalog configs/rehearsal_catalog.json --out export
python3 -m proofcall render --results runs/demo/results.json --config configs/rehearsal_realestate.json \
  --call S01:guarded:1 --out recordings/S01.mp3
```

Layout (Clean Architecture): `proofcall/domain` (pure rules, standard library only) ← `application` (agent turn, simulated call, report) ← `adapters` (Gemini, catalog tools, Edge TTS, export) ← `infrastructure` (CLI). See `SPEC.md`.

## Limits

- The rehearsal problem (a fictional real-estate project) is replaced by the official problem statement.
- Regex claim rules can block a harmless sentence (a false block). False blocks are counted and reported.
- Text-only latency is not call latency.
- The free LLM tier limits run size. Each run's size is shown in its report.
