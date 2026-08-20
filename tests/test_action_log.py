"""Per-ticket audit trail (traceability): every action an agent or human
takes on a ticket lands in out/actions.jsonl — append-only, queryable.
Contract: src/action_log.py::log_action / history."""
import json

import pytest

from src.action_log import history, log_action


def test_append_writes_complete_record(tmp_path):
    p = tmp_path / "actions.jsonl"
    rec = log_action(actor="case-worker", action="workpackage_filed",
                     tickets=["TKT-2090"], artifact="workpackages/TKT-2090.md",
                     note="statement reconciliation; playbook adapted", path=p)
    line = json.loads(p.read_text().strip())
    assert line == rec
    assert line["actor"] == "case-worker" and line["tickets"] == ["TKT-2090"]
    assert line["action"] == "workpackage_filed"
    assert "ts" in line and line["ts"][:2] == "20"      # ISO timestamp


def test_history_filters_by_ticket_in_order(tmp_path):
    p = tmp_path / "actions.jsonl"
    log_action("triage", "enriched_batch", ["TKT-2090", "TKT-2072"], path=p)
    log_action("case-worker", "workpackage_filed", ["TKT-2090"], path=p)
    log_action("liaison", "brief_filed", ["TKT-2072"], path=p)
    got = history("TKT-2090", path=p)
    assert [e["action"] for e in got] == ["enriched_batch", "workpackage_filed"]


def test_rejects_malformed_input(tmp_path):
    p = tmp_path / "actions.jsonl"
    with pytest.raises(ValueError):
        log_action("", "workpackage_filed", ["TKT-2090"], path=p)
    with pytest.raises(ValueError):
        log_action("triage", "did stuff!!", ["TKT-2090"], path=p)   # not snake_case
    with pytest.raises(ValueError):
        log_action("triage", "note", ["bogus-id"], path=p)
    assert not p.exists()
