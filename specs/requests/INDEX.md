# Request Corpus Index (P0.5.7)

Natural-language service-synthesis requests used as the "before" baseline for
macro-compression measurement. Each row maps a raw request file to its domain
and the phenomena it exercises.

Phenomena tags: `safety` `limit` `sequencing` `constraint` `eventuality` `nesting` `vague`

| file | domain | phenomena |
| --- | --- | --- |
| 01_ticketing_oversell.txt | ticketing | safety |
| 02_orders_per_call_limit.txt | orders | limit |
| 03_warehouse_auth_sequencing.txt | warehouse | sequencing |
| 04_orders_no_unpaid_ship.txt | orders/shipping | sequencing |
| 05_meetings_priority_attendees.txt | meetings/calendar | constraint |
| 06_inventory_stock_depletion.txt | inventory | safety |
| 07_hotel_reservation_eventually.txt | hotel booking | eventuality |
| 08_library_hold_within_steps.txt | library loans | eventuality |
| 09_support_close_pending_obligation.txt | support tickets | eventuality |
| 10_banking_refund_subcase.txt | banking | nesting |
| 11_procurement_nested_approval.txt | procurement/approvals | nesting |
| 12_venue_vague.txt | ticketing | vague safety |
| 13_subscription_vague.txt | subscriptions | vague |
| 14_banking_hold_limit.txt | banking holds | safety limit |
| 15_restaurant_combo.txt | restaurant reservations | sequencing safety constraint |
| 16_warehouse_combo.txt | warehouse fulfillment | limit eventuality nesting |
| 17_calendar_seq_constraint.txt | meetings/calendar | sequencing constraint |
| 18_ecommerce_cart_limit_safety.txt | e-commerce | limit safety |
| 19_lending_seq_eventuality.txt | banking/lending | sequencing eventuality |
| 20_clinic_combo_vague.txt | healthcare | vague safety sequencing eventuality |
