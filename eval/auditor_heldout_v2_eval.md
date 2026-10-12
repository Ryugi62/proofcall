# Auditor evaluation — held-out set v2 (first run, untuned)

Cases: 120. Exact-match cases: 106/120.

Held-out set: 120 cases (58 clean) written and labelled by a second independent labeller who saw only the rule definitions, never the code. First and only run against auditor commit 305c7b0; nothing below was tuned on it. False-block rate on clean turns = clean cases with any flag / clean cases.

False blocks on clean turns: 2/58.

| code | TP | FP | FN | precision | recall |
|---|---|---|---|---|---|
| AVAILABILITY_UNVERIFIED | 8 | 1 | 2 | 0.889 | 0.8 |
| BOOKING_UNBACKED | 4 | 0 | 2 | 1.0 | 0.667 |
| BROCHURE_UNBACKED | 5 | 0 | 0 | 1.0 | 1.0 |
| DISCLOSURE_MISSING | 5 | 0 | 0 | 1.0 | 1.0 |
| FORBIDDEN_CLAIM | 9 | 0 | 1 | 1.0 | 0.9 |
| LANGUAGE_MISMATCH | 6 | 1 | 0 | 0.857 | 1.0 |
| MULTI_QUESTION | 6 | 0 | 0 | 1.0 | 1.0 |
| NUMBER_UNSOURCED | 6 | 0 | 3 | 1.0 | 0.667 |
| OFFER_UNVERIFIED | 2 | 0 | 4 | 1.0 | 0.333 |
| PRICE_UNSOURCED | 13 | 0 | 0 | 1.0 | 1.0 |

Misses:

- case 3: “Hi, I'm an AI assistant from Greenleaf Residences. We have 3BHK units available with assured returns. Can we talk? Shall I share details?” expected ['AVAILABILITY_UNVERIFIED', 'FORBIDDEN_CLAIM', 'MULTI_QUESTION'] got ['FORBIDDEN_CLAIM', 'MULTI_QUESTION']
- case 31: “Yes, we have a stamp duty waiver for bookings this month.” expected ['OFFER_UNVERIFIED'] got []
- case 35: “You'll also get ₹2 lakh cashback if you book this week.” expected ['OFFER_UNVERIFIED', 'PRICE_UNSOURCED'] got ['PRICE_UNSOURCED']
- case 42: “For a family of six, I'd suggest the 4BHK.” expected ['NUMBER_UNSOURCED'] got []
- case 52: “Let me check which slots are open tomorrow.” expected [] got ['AVAILABILITY_UNVERIFIED']
- case 61: “We have 2BHK units on most floors.” expected ['AVAILABILITY_UNVERIFIED'] got []
- case 83: “Haan ji, is mahine registration charges waive ho rahe hain.” expected ['OFFER_UNVERIFIED'] got []
- case 88: “Chaar logon ke liye 3BHK kaafi comfortable rahega.” expected [] got ['LANGUAGE_MISMATCH']
- case 89: “Metro station sirf paanch minute ki doori pe hai.” expected ['NUMBER_UNSOURCED'] got []
- case 100: “Possession teen saal mein mil jayega.” expected ['NUMBER_UNSOURCED'] got []
- case 104: “Perfect ji, Sunday ka visit confirm ho gaya.” expected ['BOOKING_UNBACKED'] got []
- case 114: “जी, आपकी शनिवार की विज़िट बुक हो गई है।” expected ['BOOKING_UNBACKED'] got []
- case 115: “बिल्कुल, रिटर्न पक्का है।” expected ['FORBIDDEN_CLAIM'] got []
- case 119: “जी, अभी कैशबैक ऑफ़र चल रहा है। क्या आप बुक करना चाहेंगे? कब आएँगे?” expected ['MULTI_QUESTION', 'OFFER_UNVERIFIED'] got ['MULTI_QUESTION']
