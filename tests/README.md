# Test assets — written before any implementation (TDD)

Two layers, mirroring the spec's eval boundary (§6): the LLM layer is measured
by the golden set through `eval/run_eval.py`; the deterministic layer is
covered by pytest with exact expected values hand-verified against
`data/tickets.csv` on 2026-08-19.

## Layer 1 — `eval/golden.json` (LLM enrichment)

24 tickets across all six segments: 4 FAQ · 4 decline-incident · 4 wire-incident
(with extracted amounts $42k/$118k/$118k/$31.5k) · 4 FX-trend (the hard case:
near-identical wording weeks apart, incl. one pending ticket with no CSAT) ·
4 risk (ATO / departed controller / payroll hold / $4,850 fraud) · 4 long-tail.
Scoring rules and the severity rubric live in `_meta`. The eval-mode contract
(hard overrides OFF, few-shot ON) is recorded there so `run_eval.py` cannot
drift from spec §6.

## Layer 2 — pytest (deterministic core)

| File | Cases | Pins down (spec ref) |
|---|---|---|
| `test_burst_detector.py` | 5 | fires on 3rd ticket (TKT-2060, Aug 4 15:43); not on 2; 72h chain break; faq records never burst (statement-download FAQ bunches 4-in-72h); full run yields exactly the 14-ticket decline + 9-ticket wire incidents (§2) |
| `test_trend_detector.py` | 4 | FX trend = exactly 11 ids; vendor-payment FAQ (6 customers, 5 weeks, CSAT 3.14) must NOT trend; precedence rule — no FX mini-incident, no ticket in two clusters; <5 customers never trends (§2) |
| `test_scoring.py` | 5 | +50 risk offset exact; monotonic in severity/MRR/age; ATO ($2.4k MRR) outranks best-customer FAQ ($10.1k MRR) (§4) |
| `test_corrections.py` | 6 | hard override on; override OFF in eval mode; few-shot cap = most recent N; golden merge without duplicates; roster role-gate: only `correct_labels` authors accepted, no roster → no gate (§5, §6) |
| `test_csv_adapter.py` | 3 | 100 rows sorted; type parsing incl. None CSAT on open tickets; Aug-3 cursor → 44 tickets (§2) |
| `test_enrichment.py` | 6 | valid parse; one retry then success; twice-invalid → needs_human; few-shot corrections in prompt; known themes offered for reuse (live mode); leave-one-out — own correction never in own prompt (§4, §5) |
| `test_pipeline.py` | 3 | append-only cache: zero re-enrichment on second run; queue sorted with risk tickets pinned first; churn_risk neither pins nor earns +50 (§4) |
| `test_theme_registry.py` | 6 | merge to most-common variant; invalid canon / missing key → identity (fail open); single theme skips the LLM; examples in merge prompt; mapping applied without mutation (§4) |
| `test_metrics.py` | 7 | stuck funds dedupes follow-ups, skips resolved; risk exposure = distinct customers with open security flags; segment health; deflection ranked with hours saved; oldest open investigation age; detection lag = 1st→3rd ticket; HTML self-contained with key sections (§4) |
| `test_eval_clusters.py` | 2 | cluster-membership hit rate: perfect detection = full score; split clusters, missed trends, and false inclusion of `cluster: null` tickets all count as misses (§6) |
| `test_action_log.py` | 3 | audit trail: complete validated records; per-ticket history in order; malformed actor/action/ticket rejected before write (§3) |
| `test_skill_proposals.py` | 4 | Channel 4: propose validates verbatim target text; apply demands approve_skill_changes and edits the file; drifted targets refused; reject records reason (§5) |
| `day2/test_replay_and_writeback.py` | 4 | history/stream split 56/44; deterministic replay; write-back round trip on TKT-2072; mock Jira keys OPS-101… (§2) |
| `day2/test_watch_events.py` | 4 | INCIDENT_DECLARED triggered by TKT-2060, strictly after its arrival; seeded history is silent but counts toward clusters; RISK_PINNED for TKT-2079; cache never re-enriches a seen id (§4) |

**Total: 62 tests, all green as of 2026-08-19.**

## Protocol

- Initial state (verified): all 7 files RED with `ModuleNotFoundError` — the
  implementation does not exist yet.
- Day 1 scope: `pytest --ignore=tests/day2` must go green.
- Day 2 scope: `pytest` (everything) must go green. Day-2 tests carry the
  `day2` marker; if the mock-helpdesk time-box kills a feature, delete its
  tests in the same commit that removes it from the spec — never skip-mark
  a test to hide a cut.
- Cluster memberships in `conftest.py` are ground truth verified by direct
  CSV analysis, independent of any production code. If a detector disagrees
  with them, the detector is wrong.
