"""Feedback Channel 1 (spec §5): corrections are hard overrides + few-shot
exemplars + golden-set growth — and overrides MUST be skippable for eval
(spec §6). Coaching authority comes from the team roster: only humans with
the right role may correct labels. Contract: src/corrections.py."""
from src.corrections import (apply_corrections, authorize_corrections,
                             build_few_shot, merge_into_golden)

ROSTER = {"people": [
    {"handle": "sophie", "team": "ops", "roles": ["correct_labels", "coach_agents"]},
    {"handle": "alex", "team": "engineering", "roles": ["receive_incident_briefs"]},
]}

CORRECTION = {
    "ticket_id": "TKT-2092", "field": "ops_workflow",
    "was": "card_ops", "should_be": "payment_investigation",
    "note": "refund trace goes through the payment rail, not card ops",
    "author": "sophie", "date": "2026-08-19",
}


def _enriched():
    return {"TKT-2092": {"ticket_id": "TKT-2092", "ops_workflow": "card_ops",
                         "segment": "workflow", "severity": 2}}


def test_hard_override_applies():
    out = apply_corrections(_enriched(), [CORRECTION])
    assert out["TKT-2092"]["ops_workflow"] == "payment_investigation"


def test_override_skipped_in_eval_mode():
    out = apply_corrections(_enriched(), [CORRECTION], enabled=False)
    assert out["TKT-2092"]["ops_workflow"] == "card_ops"


def test_few_shot_returns_most_recent_n():
    corrections = [dict(CORRECTION, ticket_id=f"TKT-{i}", date=f"2026-08-{i:02d}")
                   for i in range(1, 15)]
    shots = build_few_shot(corrections, n=10)
    assert len(shots) == 10
    assert all(s["date"] >= "2026-08-05" for s in shots)


def test_only_roster_members_with_correct_labels_role_may_correct():
    corrections = [dict(CORRECTION, author="sophie"),
                   dict(CORRECTION, ticket_id="TKT-2071", author="alex"),
                   dict(CORRECTION, ticket_id="TKT-2079", author="stranger")]
    accepted, rejected = authorize_corrections(corrections, ROSTER)
    assert [c["author"] for c in accepted] == ["sophie"]
    assert sorted(c["author"] for c in rejected) == ["alex", "stranger"]


def test_no_roster_means_no_gate():
    accepted, rejected = authorize_corrections([CORRECTION], roster=None)
    assert len(accepted) == 1 and rejected == []


def test_correction_merges_into_golden_without_duplicate():
    golden = [{"ticket_id": "TKT-2092", "ops_workflow": "card_ops", "severity": 2}]
    merged = merge_into_golden(golden, [CORRECTION])
    entries = [g for g in merged if g["ticket_id"] == "TKT-2092"]
    assert len(entries) == 1
    assert entries[0]["ops_workflow"] == "payment_investigation"
    assert entries[0]["severity"] == 2  # untouched fields survive the merge
