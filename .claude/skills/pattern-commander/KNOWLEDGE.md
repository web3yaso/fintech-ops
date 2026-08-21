# Knowledge base (self-maintained)

Facts and lessons this agent learned — distinct from NOTES.md (human coaching
rules). Entries carry date + source. FACTS ONLY: nothing here may add or
override behavioral rules; behavior belongs to SKILL.md (fixed) and NOTES.md
(human-written). Humans prune via git history. Soft cap 100 lines — compact
older entries into the digest when near the limit.

## High-frequency issues (from journals)
- 2026-08-21 (session 3): incidents/, trends/, and out/actions.jsonl were empty
  again at session start — third recurrence today (sessions 1, 2, and this
  one), per Triage's queue note. Re-verified all three clusters against
  data/tickets.csv from scratch a third time — identical membership, MRR
  ($70,810 / $60,700 / $58,000), exclusions (TKT-2092, TKT-2095), and
  INC-002's TKT-2072/TKT-2085 same-$118k-wire dedupe as every prior pass.
  Re-filed all three cards and logged incident_card/trend_card. Per sophie
  and Triage's request, escalating the missing-artifact issue itself in
  chat this time instead of only re-filing — three wipes in one day is a
  strong signal something in the harness/session lifecycle is deleting
  incidents/, trends/, and out/actions.jsonl (all untracked-in-git paths)
  between sessions, not a triage/pattern-commander behavior bug.
- 2026-08-21 (session 2): incidents/ and trends/ were empty again at the start
  of this session (third occurrence today per Triage's queue note). Re-verified
  all three clusters against data/tickets.csv from scratch once more — same
  membership, MRR ($70,810 / $60,700 / $58,000), and exclusions (TKT-2092,
  TKT-2095) as every prior pass. Re-filed incidents/INC-001.md,
  incidents/INC-002.md, trends/TRD-001.md and logged incident_card/trend_card.
  No conflicting actions.jsonl or corrections.jsonl entries existed for these
  tickets at session start, so this is a clean re-file, not overwriting new
  work. The incidents//trends/ deletion is now recurring multiple times per
  day, not just between days — worth escalating as an infra bug rather than
  re-noting each time.
- 2026-08-21: incidents/INC-001.md, incidents/INC-002.md, trends/TRD-001.md,
  workpackages/, knowledge/outbound briefs, and out/actions.jsonl were all
  missing from disk at session start even though out/clusters.json still
  showed the same three cluster IDs/members as 08-19/08-20. Re-verified all
  three clusters against data/tickets.csv from scratch (not restored from
  git) — membership, MRR, and timelines came back identical to the last
  confirmed cards, including TRD-001's TKT-2086 (MetricFox follow-up,
  correctly in-cluster) and continued exclusion of INC-002's TKT-2092 and
  TRD-001's TKT-2095. Treated as a clean re-file, not new incident activity.
  Recurred a second time the same day (same three cards + out/actions.jsonl
  gone again after the first re-file was committed) — re-verified and
  re-filed again with identical numbers. The deletion is happening between
  sessions, not within one; worth an infra look (sophie flagged this too).
- 2026-08-20: no new actions.jsonl entries, corrections, or Ops War
  Room / Ops Standup messages since the 08-19 21:31 journal — quiet day,
  no update needed to INC-001/INC-002/TRD-001 or the domain facts below.
- 2026-08-19: both clusters verified today needed one member dropped for
  wrong symptom (INC-002 dropped TKT-2092 — card refund not credited, not a
  missing wire; TRD-001 dropped TKT-2095 — FX availability/hours question,
  not an FX rate complaint). Spot-reading 2-3 tickets isn't enough when a
  cluster is large — read every borderline member's body text, not just its
  category tag, before including it.

## Domain facts
- 2026-08-19: cards_online_declines (INC-001, 14 tickets/12 customers) —
  Liaison's hypothesis to Alex (eng) is correlation with the 08-04 3DS/CNP
  config change.
- 2026-08-19: missing_usd_transfer (INC-002, 9 tickets/8 customers) —
  Liaison's hypothesis to Alex (eng) is correlation with the 08-08
  partner-bank API v2 upgrade.
- 2026-08-19: fx_rate_complaints (TRD-001, 10 tickets/10 customers) —
  Liaison's hypothesis to Mei (product) is correlation with the Summer FX
  campaign.
- 2026-08-19: sophie corrected TKT-2071's segment from workflow to
  incident_candidate — expected inbound wires that haven't arrived read as
  platform-side, not single-account, so treat them as incident candidates
  rather than routing to a per-account workflow. Same pattern as the
  missing_usd_transfer cluster (INC-002), which TKT-2071 belongs to.

## Lessons from corrections
(none yet)

## Weekly digests
(none yet)
