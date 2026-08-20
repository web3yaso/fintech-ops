For: Alex Osei (engineering)

# INC-001 — Online card declines

**Status:** Prepared, pending sophie's go-ahead to file/notify (not yet escalated).

## Symptom statement
Corporate cards across 12 customers began failing specifically on
online/card-not-present (CNP) purchases (AWS, Google Ads, Shopify, Meta,
Dropbox, SaaS subscriptions) starting 2026-08-04 08:30. In-person/card-present
transactions on the same cards are unaffected. 14 tickets, avg CSAT 1.55, 3
still open.

## Affected-merchant table (by MRR)
| Customer | MRR | Tickets |
|---|---|---|
| Cobalt Robotics | $10,100 | 1 |
| NovaFleet | $9,200 | 3 |
| Summit Supply | $8,300 | 1 |
| Fieldstone Energy | $7,600 | 1 |
| Atlas Commerce | $7,100 | 1 |
| Orbit Manufacturing | $6,800 | 1 |
| Northstar Logistics | $6,200 | 1 |
| Arcadia Foods | $6,100 | 1 |
| BrightPath Health | $5,400 | 1 |
| Wavefront Media | $1,650 | 1 |
| PixelMint | $1,380 | 1 |
| Beacon Legal | $980 | 1 |

Total MRR exposed: $70,810 across 12 customers, 14 tickets.

## Timeline
- First seen: TKT-2059 (Northstar Logistics), 2026-08-04 08:30.
- Detection: cluster of same-symptom tickets across unrelated customers
  within the same day.
- Last seen: TKT-2068 (Arcadia Foods), 2026-08-07 00:27 — still open.
- Span: ~64 hours.

## Decline-context pattern
Consistently CNP/online-only; card-present transactions on the same cards
succeed throughout. No common merchant category code or BIN identified yet
from ticket text alone.

## Correlation hypothesis (SIMULATED sample — clearly a hypothesis, not confirmed)
`knowledge/inbound/eng-release-notes.md` (fabricated sample data) lists a
2026-08-04 change: "Card processor: 3DS challenge config updated for online
(CNP) transactions," owner eng-payments — same date as first-seen, same
CNP-specific symptom. Worth checking against the real deploy log, but not
confirmed as root cause.

## Evidence
Full card: `incidents/INC-001.md` (blast radius, status of all 14 tickets,
draft customer/processor escalation notes).

## Question for Alex
Does the 08-04 3DS/CNP config change line up with an actual deploy, and if
so can it be rolled back or scoped down while we confirm root cause?
