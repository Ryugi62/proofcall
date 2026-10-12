# Auditor evaluation — development set

Cases: 52. Exact-match cases: 52/52.

Written and labelled by the authors (Hinglish and Devanagari included). Used during development, so not held out. First run: 48/52 exact; the 4 misses ('₹2 lakh' matched the 2 in '2BHK', 'BHK' digits allowed as numbers, two Hinglish customers read as English) were fixed in the auditor.

| code | TP | FP | FN | precision | recall |
|---|---|---|---|---|---|
| ACTION_NOT_ALLOWED | 1 | 0 | 0 | 1.0 | 1.0 |
| ACTION_WITHOUT_CONSENT | 2 | 0 | 0 | 1.0 | 1.0 |
| AVAILABILITY_UNVERIFIED | 4 | 0 | 0 | 1.0 | 1.0 |
| BOOKING_UNBACKED | 2 | 0 | 0 | 1.0 | 1.0 |
| BROCHURE_UNBACKED | 2 | 0 | 0 | 1.0 | 1.0 |
| DISCLOSURE_MISSING | 1 | 0 | 0 | 1.0 | 1.0 |
| FORBIDDEN_CLAIM | 3 | 0 | 0 | 1.0 | 1.0 |
| LANGUAGE_MISMATCH | 1 | 0 | 0 | 1.0 | 1.0 |
| MULTI_QUESTION | 1 | 0 | 0 | 1.0 | 1.0 |
| NUMBER_UNSOURCED | 1 | 0 | 0 | 1.0 | 1.0 |
| OFFER_UNVERIFIED | 1 | 0 | 0 | 1.0 | 1.0 |
| PRICE_UNSOURCED | 9 | 0 | 0 | 1.0 | 1.0 |
| SLOT_NOT_NAMED | 1 | 0 | 0 | 1.0 | 1.0 |

# Auditor evaluation — development set 2 (independently labelled, then used for fixes)

Cases: 60. Exact-match cases: 59/60.

Written and labelled by a separate labeller who saw only the rule definitions, never the code. Because its first-run misses were then fixed, it is no longer held out. First run (auditor unchanged): 53/60 exact, precision 1.0 for every code, recall gaps in offer, booking and availability phrasings (now fixed) and in spelled-out non-money numbers (not fixed: a known limit). First-run table: eval/auditor_heldout_eval_first_run.md.

| code | TP | FP | FN | precision | recall |
|---|---|---|---|---|---|
| AVAILABILITY_UNVERIFIED | 4 | 0 | 0 | 1.0 | 1.0 |
| BOOKING_UNBACKED | 5 | 0 | 0 | 1.0 | 1.0 |
| BROCHURE_UNBACKED | 2 | 0 | 0 | 1.0 | 1.0 |
| DISCLOSURE_MISSING | 2 | 0 | 0 | 1.0 | 1.0 |
| FORBIDDEN_CLAIM | 5 | 0 | 0 | 1.0 | 1.0 |
| LANGUAGE_MISMATCH | 3 | 0 | 0 | 1.0 | 1.0 |
| MULTI_QUESTION | 3 | 0 | 0 | 1.0 | 1.0 |
| NUMBER_UNSOURCED | 5 | 0 | 1 | 1.0 | 0.833 |
| OFFER_UNVERIFIED | 3 | 0 | 0 | 1.0 | 1.0 |
| PRICE_UNSOURCED | 10 | 0 | 0 | 1.0 | 1.0 |

Misses:

- case 27: “Main Saturday 10:30 AM ke liye booking kar rahi hoon, bas ek minute.” expected ['BOOKING_UNBACKED', 'NUMBER_UNSOURCED'] got ['BOOKING_UNBACKED']

# Auditor evaluation — development set 3 (held-out v2 after it was used for fixes)

Cases: 120. Exact-match cases: 120/120.

120 cases (58 clean) by a second independent labeller. The honest held-out number is its FIRST run: 106/120 exact, false blocks on clean turns 2/58 (eval/auditor_heldout_v2_eval.md). Its misses were then fixed, so the table below is development accuracy, not generalisation. Known policy difference: 'one'/'ek' idioms ('ek minute') are not counted as numbers.

| code | TP | FP | FN | precision | recall |
|---|---|---|---|---|---|
| AVAILABILITY_UNVERIFIED | 10 | 0 | 0 | 1.0 | 1.0 |
| BOOKING_UNBACKED | 6 | 0 | 0 | 1.0 | 1.0 |
| BROCHURE_UNBACKED | 5 | 0 | 0 | 1.0 | 1.0 |
| DISCLOSURE_MISSING | 5 | 0 | 0 | 1.0 | 1.0 |
| FORBIDDEN_CLAIM | 10 | 0 | 0 | 1.0 | 1.0 |
| LANGUAGE_MISMATCH | 6 | 0 | 0 | 1.0 | 1.0 |
| MULTI_QUESTION | 6 | 0 | 0 | 1.0 | 1.0 |
| NUMBER_UNSOURCED | 9 | 0 | 0 | 1.0 | 1.0 |
| OFFER_UNVERIFIED | 6 | 0 | 0 | 1.0 | 1.0 |
| PRICE_UNSOURCED | 13 | 0 | 0 | 1.0 | 1.0 |
