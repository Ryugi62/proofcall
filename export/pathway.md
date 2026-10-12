# Pathway

```mermaid
flowchart LR
  opening -- agrees_to_talk --> qualify
  opening -- wrong_person --> close
  opening -- call_later --> close
  qualify -- ask_price --> pitch
  qualify -- ask_availability --> pitch
  qualify -- not_interested --> close
  pitch -- objection_price --> objection
  pitch -- want_visit --> visit_booking
  pitch -- want_brochure --> followup
  objection -- want_visit --> visit_booking
  objection -- want_brochure --> followup
  objection -- not_interested --> close
  visit_booking -- booked --> close
  visit_booking -- declines --> close
  followup -- sent --> close
  followup -- declines --> close
```
