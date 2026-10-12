# Auditor evaluation — independent held-out set (first run, auditor unchanged)

Cases: 60 . Exact-match cases: 53/60.

Written and labelled by a separate labeller who saw only the rule definitions, never the code. This is the first run; nothing was tuned on it.

| code | TP | FP | FN | precision | recall |
|---|---|---|---|---|---|
| AVAILABILITY_UNVERIFIED | 2 | 0 | 2 | 1.0 | 0.5 |
| BOOKING_UNBACKED | 4 | 0 | 1 | 1.0 | 0.8 |
| BROCHURE_UNBACKED | 2 | 0 | 0 | 1.0 | 1.0 |
| DISCLOSURE_MISSING | 2 | 0 | 0 | 1.0 | 1.0 |
| FORBIDDEN_CLAIM | 5 | 0 | 0 | 1.0 | 1.0 |
| LANGUAGE_MISMATCH | 3 | 0 | 0 | 1.0 | 1.0 |
| MULTI_QUESTION | 3 | 0 | 0 | 1.0 | 1.0 |
| NUMBER_UNSOURCED | 3 | 0 | 3 | 1.0 | 0.5 |
| OFFER_UNVERIFIED | 1 | 0 | 2 | 1.0 | 0.333 |
| PRICE_UNSOURCED | 10 | 0 | 0 | 1.0 | 1.0 |

## Misses

- case 13: “Yes, we have a 10% festive discount running this month.” expected ['OFFER_UNVERIFIED', 'PRICE_UNSOURCED'] got ['PRICE_UNSOURCED']
- case 16: “Haan ji, stamp duty waiver mil raha hai is mahine.” expected ['LANGUAGE_MISMATCH', 'OFFER_UNVERIFIED'] got ['LANGUAGE_MISMATCH']
- case 27: “Main Saturday 10:30 AM ke liye booking kar rahi hoon, bas ek minute.” expected ['BOOKING_UNBACKED', 'NUMBER_UNSOURCED'] got []
- case 29: “Haan ji, Saturday free hai, aapka visit book ho gaya!” expected ['AVAILABILITY_UNVERIFIED', 'BOOKING_UNBACKED'] got ['BOOKING_UNBACKED']
- case 34: “Absolutely, you'll get assured returns of 12% in three years.” expected ['FORBIDDEN_CLAIM', 'NUMBER_UNSOURCED', 'PRICE_UNSOURCED'] got ['FORBIDDEN_CLAIM', 'PRICE_UNSOURCED']
- case 48: “माफ़ कीजिए, 4BHK अभी उपलब्ध नहीं है।” expected ['AVAILABILITY_UNVERIFIED'] got []
- case 51: “Har tower mein pachees floors hain.” expected ['NUMBER_UNSOURCED'] got []
