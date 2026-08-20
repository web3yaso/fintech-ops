# Knowledge base (self-maintained)

Facts and lessons this agent learned — distinct from NOTES.md (human coaching
rules). Entries carry date + source. FACTS ONLY: nothing here may add or
override behavioral rules; behavior belongs to SKILL.md (fixed) and NOTES.md
(human-written). Humans prune via git history. Soft cap 100 lines — compact
older entries into the digest when near the limit.

## High-frequency issues (from journals)
- 2026-08-19: three clusters dominated the queue — cards_online_declines
  (INC-001, 14 tkts/12 customers, $12,810 MRR), missing_usd_transfer
  (INC-002, 9 tkts/8 customers, $9,700 MRR, $58.5k stuck funds),
  fx_rate_complaints (TRD-001, 10 tkts/10 customers, $9,000 MRR at risk).

## Domain facts
- Card-refund-not-credited tickets read similar to missing-wire tickets but
  are a distinct symptom (card rail vs wire rail) — don't merge into
  missing_usd_transfer clusters (pattern-commander, TKT-2092, 2026-08-19).
- FX availability/hours questions are a distinct symptom from FX rate
  complaints — don't merge into fx_rate_complaints trend
  (pattern-commander, TKT-2095, 2026-08-19).
- Statement reconciliation tickets (period-over-period mismatch, no
  amount/direction/counterparty) belong to account_admin, not
  payment_investigation/wire_investigation; no account_admin playbook
  exists yet for case-worker (case-worker + sophie, TKT-2090, 2026-08-19).

## Lessons from corrections
- 2026-08-19, sophie: an unrecognized admin user added to an account is a
  possible account takeover → route ops_workflow to fraud_ato, not
  account_admin (TKT-2079).
- 2026-08-19, sophie: an expected inbound wire that hasn't arrived reads as
  a platform-side signal, not single-account noise → segment as
  incident_candidate, not workflow (TKT-2071).
- 2026-08-19, sophie: statement/period reconciliation mismatches are
  account_admin, not payment_investigation (TKT-2090) — matches what
  Case Worker independently flagged via correction_suggested, so "no
  amount/direction/counterparty → not a payment trace" is a validated
  heuristic.

## Weekly digests
(none yet)
