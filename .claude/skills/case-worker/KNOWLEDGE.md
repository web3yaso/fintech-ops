# Knowledge base (self-maintained)

Facts and lessons this agent learned — distinct from NOTES.md (human coaching
rules). Entries carry date + source. FACTS ONLY: nothing here may add or
override behavioral rules; behavior belongs to SKILL.md (fixed) and NOTES.md
(human-written). Humans prune via git history. Soft cap 100 lines — compact
older entries into the digest when near the limit.

## High-frequency issues (from journals)
- 2026-08-19: `account_admin` has no shipped playbook, and it's already the target of two relabels today (TKT-2090 payment_investigation→account_admin by me/sophie; TKT-2079 account_admin→fraud_ato by sophie, unrecognized admin user = possible ATO). Expect more payment_investigation tickets that are actually statement/access issues — keep flagging via `correction_suggested` and best-effort packages rather than waiting on a playbook.

## Domain facts
- Statement/reconciliation complaints (no amount, direction, or counterparty in the ticket text) don't fit `wire_investigation` — route as `account_admin` even though no playbook exists yet; a best-effort flagged package is correct until sophie/marcus confirm the relabel (TKT-2090, 2026-08-19).
- A ticket already `resolved` in-system with low CSAT (e.g. CSAT 1) can mean the fix didn't land with the customer, not that the ticket is unworked — check internal resolution notes before treating it as fresh (TKT-2090, 2026-08-19).
- An unrecognized admin user on an account is a possible account-takeover signal and belongs to `fraud_ato`, not `account_admin` (sophie's correction on TKT-2079, 2026-08-19) — relevant if a similar symptom shows up on a ticket routed to me.

## Lessons from corrections
- 2026-08-19 (sophie, via triage): my `correction_suggested` on TKT-2090 (payment_investigation → account_admin, "statement reconciliation not payment trace") was confirmed verbatim same-turn — the heuristic "no amount/direction/counterparty in ticket text → not a wire case" is validated, keep using it.

## Weekly digests
(none yet)
