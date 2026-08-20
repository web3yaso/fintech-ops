"""Skill-change proposals: agents may PROPOSE edits to any SKILL.md but never
apply them — only a human holding `approve_skill_changes` applies (by running
the CLI themselves). Contract: src/skill_proposals.py."""
import json

import pytest

from src.skill_proposals import apply_proposal, list_pending, propose, reject

ROSTER = {"people": [
    {"handle": "sophie", "roles": ["approve_skill_changes"]},
    {"handle": "alex", "roles": []},
]}


@pytest.fixture()
def skill_file(tmp_path):
    d = tmp_path / ".claude/skills/ticket-triage"
    d.mkdir(parents=True)
    f = d / "SKILL.md"
    f.write_text("# Triage\n\nPoll every 1 second.\n")
    return tmp_path


def test_propose_validates_target_text(skill_file, tmp_path):
    p = tmp_path / "proposals.jsonl"
    rec = propose("ticket-triage", "ticket-triage", "Poll every 1 second.",
                  "Poll every 2 seconds.", "1s polling wastes tokens",
                  root=skill_file, path=p)
    assert rec["id"] == "SCP-001" and rec["status"] == "proposed"
    with pytest.raises(ValueError):
        propose("ticket-triage", "ticket-triage", "TEXT NOT IN FILE", "x",
                "r", root=skill_file, path=p)


def test_apply_requires_role_and_edits_file(skill_file, tmp_path):
    p = tmp_path / "proposals.jsonl"
    rec = propose("ticket-triage", "ticket-triage", "Poll every 1 second.",
                  "Poll every 2 seconds.", "cost", root=skill_file, path=p)
    with pytest.raises(PermissionError):
        apply_proposal(rec["id"], "alex", ROSTER, root=skill_file, path=p)
    applied = apply_proposal(rec["id"], "sophie", ROSTER, root=skill_file, path=p)
    assert applied["status"] == "approved" and applied["approver"] == "sophie"
    text = (skill_file / ".claude/skills/ticket-triage/SKILL.md").read_text()
    assert "Poll every 2 seconds." in text and "Poll every 1 second." not in text
    assert list_pending(path=p) == []


def test_apply_refuses_if_target_drifted(skill_file, tmp_path):
    p = tmp_path / "proposals.jsonl"
    rec = propose("ticket-triage", "ticket-triage", "Poll every 1 second.",
                  "Poll every 2 seconds.", "cost", root=skill_file, path=p)
    f = skill_file / ".claude/skills/ticket-triage/SKILL.md"
    f.write_text(f.read_text().replace("1 second", "5 seconds"))  # human edited meanwhile
    with pytest.raises(ValueError):
        apply_proposal(rec["id"], "sophie", ROSTER, root=skill_file, path=p)


def test_reject_records_reason(skill_file, tmp_path):
    p = tmp_path / "proposals.jsonl"
    rec = propose("liaison", "ticket-triage", "Poll every 1 second.",
                  "Never poll.", "why not", root=skill_file, path=p)
    out = reject(rec["id"], "sophie", ROSTER, "breaks live mode", path=p)
    assert out["status"] == "rejected" and out["reason"] == "breaks live mode"
    assert list_pending(path=p) == []
