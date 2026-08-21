# Knowledge base (self-maintained)

Facts and lessons this agent learned — distinct from NOTES.md (human coaching
rules). Entries carry date + source. FACTS ONLY: nothing here may add or
override behavioral rules; behavior belongs to SKILL.md (fixed) and NOTES.md
(human-written). Humans prune via git history. Soft cap 100 lines — compact
older entries into the digest when near the limit.

## High-frequency issues (from journals)
- 2026-08-21: `knowledge/outbound/eng/` and `knowledge/outbound/product/` were empty on disk at task start — the three 2026-08-19 briefs (INC-001, INC-002, TRD-001) were gone, same as the incidents/trends/workpackages vanishing that Triage, Pattern Commander, and Case Worker all flagged today. Re-filed all three verbatim from the re-filed cards (OPS-101 for INC-001, OPS-102 for INC-002); TRD-001 brief has no tracker issue by design (trends go to product, not the tracker). Fourth independent flag today of the same vanishing-files symptom — worth an infra look.
- 2026-08-20: Quiet day — no Liaison actions in out/actions.jsonl, no entries in feedback/corrections.jsonl, no room messages past 2026-08-19T19:38 across any bot thread (checked via GET /api/bots). Nothing to distill; carrying forward 2026-08-19 entries below unchanged.
- 2026-08-19: Escalation filing/notification consistently held pending sophie's `approve_escalations` go-ahead — draft the brief immediately, but wait to file the tracker issue or @mention the owner. Filed 3 briefs today (INC-001, INC-002, TRD-001), all held.
- 2026-08-19: Restricted-account escalations (e.g. TKT-2081) hit a data gap: ticket text has no internal hold-reason field, only "dashboard says restricted." Compliance (Raj) needs the real reason pulled by sophie/marcus or via a Case Worker deep-dive before compliance can clear it.

## Domain facts
- 2026-08-19: NOTES.md rule added by Raj (compliance, `coach_agents`): CC compliance on any escalation brief touching a restricted account or sanctions flag.
- 2026-08-19: Correlation hypotheses used in today's briefs — INC-001 (card CNP declines) ↔ 08-04 CNP/3DS config change; INC-002 (missing wires) ↔ 08-08 partner-bank API v2 upgrade; TRD-001 (FX complaints) only partially overlaps the Summer FX campaign window — don't claim full correlation when evidence only partially fits.

## Lessons from corrections
- 2026-08-19: No correction was directed at Liaison today. Adjacent triage corrections worth remembering for future clustering: "expected wires that haven't arrived" reads as platform-side/incident (not single-account workflow) — TKT-2071 was reclassified this way and folded into INC-002.

## Weekly digests
(none yet)
