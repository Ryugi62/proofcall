# Variables

Source `tool` = may only be filled by a function result. Source `customer` = captured from the customer's words. `post_call` = extracted after the call.

| variable | type | source | required | validation / meaning |
|---|---|---|---|---|
| `customer_name` | string | constant | yes | Pre-call lead name |
| `lead_source` | string | constant | yes | Where the enquiry came from |
| `lead.phone` | string | constant | yes | Number dialled (platform context) |
| `call_id` | string | constant | yes | Platform call id |
| `agent_name` | string | constant | yes | Asha |
| `project_name` | string | constant | yes | Greenleaf Residences |
| `lead.language` | enum[en,hinglish,hi] | customer | yes | Language the customer speaks; agent mirrors it |
| `lead.bhk` | enum[2bhk,3bhk,4bhk] | customer | yes | Configuration asked (one of 2bhk, 3bhk, 4bhk) |
| `lead.budget_inr` | integer | customer |  | Budget normalised to rupees (post-call extraction) |
| `lead.timeline` | enum[0-3m,3-6m,6m+,unknown] | customer |  |  |
| `get_price.price_from_inr` | integer_inr | tool |  | Starting price in rupees (for budget comparison) |
| `get_price.say` | text | tool |  | Exact sentence to speak, includes GST note |
| `check_units.units_left` | integer | tool |  |  |
| `check_units.say` | text | tool |  |  |
| `check_slots.slots` | list[text] | tool |  |  |
| `check_slots.first_slot` | text | tool |  | Slot named in the consent question |
| `get_offer.offer` | text | tool |  | Live offer or 'none' |
| `book_site_visit.booking_id` | text | tool |  | Only set on success; backs every 'booked' claim |
| `send_brochure.sent` | boolean | tool |  | Backs every 'brochure sent' claim |
| `mark_dnd.dnd` | boolean | tool |  | Opt-out recorded |
| `schedule_callback.when` | text | tool |  |  |
| `lead.temperature` | enum[hot,warm,cold] | post_call | yes |  |
| `conversion_reason` | enum[visit_booked,brochure_sent,transferred,callback,none] | post_call | yes |  |
| `dropoff_reason` | enum[wrong_person,not_interested,price,sold_out,opt_out,call_later,none] | post_call | yes |  |
| `guardrail_blocks` | integer | post_call |  | Turns blocked by the auditor (from the audit log) |
| `record_consent.consent_id` | string | tool |  | Issued only for a clear yes; required by book_site_visit / send_brochure |
| `record_consent.question` | text | tool |  | The exact yes/no question the yes answered |
| `record_consent.recorded_at` | iso_datetime | tool |  |  |
| `book_site_visit.slot_iso` | iso_datetime | tool |  |  |
| `cancel_booking.cancelled` | string | tool |  | Booking id cancelled after a withdrawal |
| `budget_gap` | boolean | post_call | yes | Budget stated below get_price.price_from_inr |
| `objection_reason` | enum[price,location,timing,trust,none] | post_call | yes |  |
| `call_language` | enum[en,hinglish,hi] | post_call | yes |  |
