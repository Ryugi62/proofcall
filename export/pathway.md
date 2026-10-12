# Pathway

```mermaid
flowchart LR
  opening -- agrees_to_talk --> qualify
  opening -- ask_price --> pitch
  opening -- ask_availability --> pitch
  opening -- wrong_person --> close
  opening -- call_later --> close
  opening -- opt_out --> close
  opening -- refuse_recording --> close
  qualify -- ask_price --> pitch
  qualify -- ask_availability --> pitch
  qualify -- not_interested --> close
  pitch -- objection_price --> objection
  pitch -- want_visit --> visit_booking
  pitch -- want_brochure --> followup
  pitch -- sold_out --> objection
  pitch -- opt_out --> close
  pitch -- call_later --> close
  objection -- want_visit --> visit_booking
  objection -- want_brochure --> followup
  objection -- not_interested --> close
  objection -- call_later --> close
  objection -- opt_out --> close
  visit_booking -- booked --> close
  visit_booking -- declines --> objection
  visit_booking -- revoke_consent --> close
  followup -- sent --> close
  followup -- declines --> close
```
