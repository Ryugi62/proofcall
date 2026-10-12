# ProofCall — SPEC (v0.1, 2026-10-12)

## 0. One line
A voice calling agent for enterprise conversations (pricing, availability, explicit consent) whose guardrails are **enforced and measured, not requested**: the language model writes slots, values are rendered from tool results, a deterministic validator audits every agent turn, and a simulated-customer test suite reports violations against a prompt-only baseline.
Essence: not "a natural-sounding bot", but "a call agent that can prove it never misquotes a price, invents availability, or acts without consent".

## 1. Success conditions · deadline · non-goals
- Reference: commercial voice-agent platforms test with simulated callers (see README "Similar tools"); hackathon entries typically ship 5–6 scenarios with pass/fail and prompt-only guardrails.
- Success (numbers):
  - S1 Suite: ≥12 self-designed simulated-customer scenarios, ≥5 edge cases, each run ≥3 times.
  - S2 Guarded agent: 0 guardrail violations across all agent turns of the suite; prompt-only baseline run on the same scenarios is reported next to it (violations counted by the same auditor).
  - S3 Task success (expected outcome reached) ≥ 90 % of guarded runs.
  - S4 Agent turn length mean ≤ 25 words; per-turn processing latency (LLM + tools + validator) median reported, target ≤ 1.5 s; validator overhead median ≤ 5 ms.
  - S5 Two recordings: one successful task, one failure-mode handling, both untouched suite runs, both sides synthetic voices.
- Deadline: contest submission 2026-10-26 23:59 IST (internal 2026-10-25 23:59 IST).
- Non-goals: training speech or language models; real outbound calls to real people; telephony infrastructure; a UI.

## 2. Constraints
- Contest text: "autonomous voice agent bound by strict guardrails around pricing, availability, and explicit consent claims … at least five custom-designed simulated customer scenarios, intentionally targeting realistic failure modes … exported agent configuration alongside two complete call recordings".
- Cost: 0 — free LLM tier (Gemini API) and free neural TTS; rate limits are respected by the runner (retry with backoff).
- Privacy: no real personal data; all customers are simulated; no human voice in recordings.

## 3. Ubiquitous language
| Term | Meaning | Code name |
|---|---|---|
| Agent config | States, variables, tools, intents, rules, fallbacks — the exported artifact | `AgentConfig` |
| State | A conversation stage with goal, instructions, allowed actions and transitions | `State` |
| Variable | Typed value with a source (`tool`, `customer`, `constant`) | `Variable` |
| Slot | `{{name}}` placeholder written by the model, filled from the variable store | `render_slots` |
| Variable store | Values set during one call, each with its source | `VariableStore` |
| Consent ledger | Verbatim customer consent per purpose, with revocation | `ConsentLedger` |
| Guardrail auditor | Deterministic per-turn check of spoken text and action | `audit_turn` |
| Violation | One guardrail breach in one agent turn (code + evidence) | `Violation` |
| Fallback utterance | Safe per-state line spoken when a turn is blocked | `State.fallback` |
| Scenario | Simulated customer persona, goal, tactics, expected outcome | `Scenario` |
| Call record | Turns, events, outcome, latencies of one simulated call | `CallRecord` |
| Guarded / baseline | Same prompts; guarded renders slots and blocks violations, baseline speaks freely and is only audited | `mode` |
| Violation rate | violations ÷ agent turns, over a set of calls | `violation_rate` |

## 4. Domain model
- Aggregate `AgentConfig` (value objects `State`, `Variable`, `Tool`, `Intent`).
- `VariableStore`, `ConsentLedger` (entities scoped to one call).
- Domain services: `render_slots`, `audit_turn`, `detect_consent`, `detect_revocation`, `extract_numbers`, `next_state`.
- Ports (application): `LanguageModel.complete(system, messages) -> str`, `ToolBackend.call(name, args) -> dict`, `Clock.now() -> float`, `SpeechRenderer.render(call_record, path)`.

## 5. Use cases
| UC | Input | Output | Rule |
|---|---|---|---|
| UC-1 agent turn | config, state, history, store, ledger, mode | spoken text, action, events, latency | guarded: render + audit + fallback on violation; baseline: audit only |
| UC-2 simulated call | scenario, agent, customer model | `CallRecord` | stop on end_call, customer hang-up or max turns |
| UC-3 suite | scenarios × runs × modes | JSON results + Markdown report | numbers in the report are generated from results only |
| UC-4 export | config | platform-neutral JSON + prompt Markdown + variable table | export is generated from the same config the runner used |
| UC-5 recording | call record | WAV/MP3 with two synthetic voices + transcript | gaps between turns = measured processing latency |

## 6. Acceptance criteria
- AC-1 Given a spoken text with a number not present in any tool-sourced variable, When audited, Then a `PRICE_UNSOURCED` (currency/amount) or `NUMBER_UNSOURCED` violation is returned.
- AC-2 Given the same number present in a tool-sourced variable, When audited, Then no number violation.
- AC-3 Given an availability claim before any availability tool result exists in the call, When audited, Then `AVAILABILITY_UNVERIFIED`.
- AC-4 Given a consent-gated action without a non-revoked consent for its purpose, When audited, Then `ACTION_WITHOUT_CONSENT`; with consent recorded from a verbatim affirmative customer quote, Then none.
- AC-5 Given a consent quote that is negative ("no", "nahi", "don't") or not present in the last customer utterance, When recording consent, Then it is rejected.
- AC-6 Given a customer revocation after consent, When the ledger processes it, Then the consent is revoked and later gated actions violate.
- AC-7 Given a forbidden claim phrase from config (e.g. "guaranteed"), When audited, Then `FORBIDDEN_CLAIM`.
- AC-8 Given the first agent turn of a call without the configured disclosure phrase, When audited, Then `DISCLOSURE_MISSING`.
- AC-9 Given slot text `{{price.basic.monthly}}` and the variable set by a tool, When rendered, Then the value appears; unknown slot → `SLOT_UNFILLED` and the guarded agent speaks the state fallback.
- AC-10 Given an action not allowed in the current state, When audited, Then `ACTION_NOT_ALLOWED`.
- AC-11 Given guarded mode and a violating draft, When the turn completes, Then the spoken text is the fallback, the draft and violations are logged as a `blocked` event, and the spoken text has 0 violations.
- AC-12 Given suite results, When the report is built, Then every number in the report is computed from the results file (test asserts totals).
- AC-13 Given a config file, When exported, Then the export contains states, prompts, variables (with source and type), tools, intents, guardrails.

## 7. Architecture
```
proofcall/domain  ←  proofcall/application  ←  proofcall/adapters (gemini, tools_mock, edge_tts, export)  ←  proofcall/infrastructure (cli, composition)
```
Domain imports nothing outside the standard library.

## 8. Non-functional
Validator is pure and deterministic (regex + set lookups). Runner logs every LLM call latency. Retries with exponential backoff on HTTP 429/5xx.

## 9. Physical verification
- Run the suite against the live free LLM; store `runs/<id>/results.json`, `report.md`.
- Render two recordings and listen-check durations, turn gaps, and that both voices are synthetic.
- Open the public Drive folder and repo in a logged-out browser before submission.

## 10. Change log
- v0.1 2026-10-12 first version (rehearsal problem: rooftop-solar site-survey booking; replaced by the official problem statement on 2026-10-13).
