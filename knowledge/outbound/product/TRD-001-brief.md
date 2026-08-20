For: Mei Tanaka (product, FX pricing owner)

# TRD-001 — FX rate complaints (slow burn)

**Status:** Prepared, pending sophie's go-ahead to file/notify (not yet escalated).

## Summary
Customers converting CAD/other currencies to USD consistently flag the FX
rate as worse than market/Google rate, spanning 2026-07-20 to 2026-08-07
(~18 days, still active as of last-seen). This is a pricing/spread question,
not an outage. 10 verified tickets (TKT-2095 dropped as a mis-cluster — see
below), 10 customers, $58,000 MRR at risk.

## Customer-voice quote sheet
- "The USD rate in the app is noticeably worse than what I see online. Can
  someone explain the difference?" — Northstar Logistics (TKT-2049),
  NovaFleet (TKT-2054)
- "We converted about $75k CAD to USD and the rate looks expensive. What
  spread are we paying?" — MetricFox (TKT-2050), Orbit Manufacturing (TKT-2055)
- "Why is my exchange rate different from Google? I need to understand the
  fees before our next conversion." — Atlas Commerce (TKT-2051), Cobalt
  Robotics (TKT-2056)
- "We do a lot of USD purchases and the current conversion rate is becoming
  hard to justify. Can you review it?" — Summit Supply (TKT-2053), TrueNorth
  Travel (TKT-2058)
- "Following up on my exchange-rate question. I still do not understand why
  the rate is so far from the market rate." — MetricFox (TKT-2086)

Note: several quotes are near-identical across different customers —
possibly templated complaint language (e.g. shared finance-team advisor)
rather than fully independent reports, though customers/companies are
distinct.

## MRR at risk
$58,000 across 10 customers. CSAT on the 9 resolved/scored tickets averages
1.67 (range 1–2); 2 tickets still pending with no CSAT yet.

## Competitive framing (quoted from tickets)
Customers are benchmarking against "what I see online" / "the market rate" /
"Google" — i.e. an external mid-market reference rate, not a competitor
product by name.

## Correlation hypothesis (SIMULATED sample — clearly a hypothesis, not confirmed)
`knowledge/inbound/marketing-campaign-calendar.md` (fabricated sample data)
lists a "Summer FX" rate-awareness email campaign to SMBs, 2026-07-15 →
07-31, expected effect "more FX pricing questions." The campaign window
overlaps the first half of this trend's span (07-20 onward) and could
plausibly explain part of the early volume — but the trend continues well
past 07-31 (last-seen 08-07) and is not fully explained by campaign timing
alone.

## Correction noted
TKT-2095 (Crescent Apparel, "Can we convert CAD to USD outside regular
business hours?") was originally clustered here but is an availability
question, not a rate complaint — dropped. Its earlier timestamp
(2026-07-03) was setting the cluster's original first-seen, which no longer
applies once removed.

## Evidence
Full card: `trends/TRD-001.md`.

## Suggested next step (recommendation, not a decision)
Check whether the current CAD→USD spread is out of line with the
market/Google benchmark customers are citing, and whether proactive
rate-transparency messaging (e.g. showing the spread at time of conversion)
would reduce ticket volume.
