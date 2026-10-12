# Variables

Source `tool` = may only be filled by a function result. Source `customer` = captured from the customer's words. `post_call` = extracted after the call.

| variable | type | source | required | validation / meaning |
|---|---|---|---|---|
| `customer_name` | string | constant | yes | Pre-call lead name |
| `lead_source` | string | constant |  | Where the enquiry came from |
| `lead.bhk` | enum[2bhk,3bhk,4bhk] | customer |  | Configuration asked |
| `lead.budget` | string | customer |  | Budget in customer's words |
| `lead.timeline` | enum[0-3m,3-6m,6m+,unknown] | customer |  |  |
| `price.<bhk>.from` | money_inr | tool |  | Starting price, set by get_price |
| `price.<bhk>.booking_amount` | money_inr | tool |  | Booking amount, set by get_price |
| `availability.units.<bhk>` | integer | tool |  | Units left, set by check_units |
| `availability.slots` | list[datetime_text] | tool |  | Visit slots, set by check_slots |
| `offer.current` | string | tool |  | Live offer text or 'none', set by get_offer |
| `booking.id` | string | tool |  | Set by book_site_visit |
| `booking.slot` | datetime_text | tool |  |  |
| `consent.site_visit` | verbatim_quote | customer |  | affirmative, present in last customer utterance, not revoked |
| `consent.whatsapp` | verbatim_quote | customer |  | affirmative, present in last customer utterance, not revoked |
| `lead.temperature` | enum[hot,warm,cold] | post_call |  |  |
| `conversion_reason` | enum[visit_booked,brochure_sent,transferred,none] | post_call |  |  |
| `dropoff_reason` | enum[wrong_person,not_interested,price,availability,opt_out,call_later,none] | post_call |  |  |
| `brochure.sent` | enum[yes] | tool |  | Set by send_brochure |
