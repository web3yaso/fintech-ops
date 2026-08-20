For: Alex Osei (engineering)

# INC-002 — Missing/delayed incoming USD wire transfers

**Status:** Prepared, pending sophie's go-ahead to file/notify (not yet escalated).

## Symptom statement
Incoming USD wires are not landing in accounts within the expected window
(senders confirm send, funds not visible 24h+ later), affecting 8 customers,
several blocking payroll/supplier payments, starting 2026-08-08. 9 verified
tickets (TKT-2092 dropped as a mis-cluster — see below), avg CSAT (resolved
subset) 1.75.

## Affected-merchant table (by MRR)
| Customer | MRR | Tickets | Stuck amount (from ticket text) |
|---|---|---|---|
| Cobalt Robotics | $10,100 | 2 (TKT-2072, TKT-2085) | $118k (same wire, referenced twice) |
| NovaFleet | $9,200 | 1 | $42,000 |
| Summit Supply | $8,300 | 1 | $64,000 |
| Fieldstone Energy | $7,600 | 1 | $31,500 |
| Atlas Commerce | $7,100 | 1 | not stated |
| Orbit Manufacturing | $6,800 | 1 | $87,000 |
| Copperline Construction | $6,400 | 1 | not stated |
| TrueNorth Travel | $5,200 | 1 | not stated |

Total MRR exposed: $60,700 across 8 customers, 9 tickets.
Total stuck funds identified in ticket text (deduped): $342,500.

## Timeline
- First seen: TKT-2071 (NovaFleet), 2026-08-08 09:15 — "$42,000 USD sent
  yesterday, still not showing."
- Detection: second wire-delay ticket same day (TKT-2072, Cobalt Robotics,
  $118k) plus escalating follow-up (TKT-2085).
- Last seen: TKT-2078 (TrueNorth Travel), 2026-08-11 14:15.
- Span: ~77 hours.

## Decline-context pattern
Not a decline — a posting delay on inbound USD wires specifically. Two
open cases (Cobalt Robotics $118k, Fieldstone Energy $31,500) explicitly
tied to payroll deadlines.

## Correlation hypothesis (SIMULATED sample — clearly a hypothesis, not confirmed)
`knowledge/inbound/eng-release-notes.md` (fabricated sample data) lists a
2026-08-08 change: "Partner-bank API client upgraded to v2 (inbound posting
webhooks)," owner eng-payments — same date as first-seen, and directly
touches inbound posting. Worth checking against the real deploy log, but not
confirmed as root cause.

## Correction noted
TKT-2092 (Harbor & Pine, "merchant refund not credited to card") was
originally clustered here but is a card-refund issue, not an incoming-wire
issue — dropped. Flagged to Triage to split "card refund delay" from
"incoming wire delay" as separate themes going forward.

## Evidence
Full card: `incidents/INC-002.md` (blast radius, status of all 9 tickets,
draft customer/banking-partner escalation notes).

## Question for Alex
Does the 08-08 partner-bank API v2 upgrade (inbound posting webhooks) match
an actual deploy, and could it be dropping or delaying inbound posting
events for a subset of accounts?
