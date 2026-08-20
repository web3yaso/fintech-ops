"""Day-2 scope: --watch mode event stream (spec §4).
Contract: src/watch.py::process_stream(records_iter, sink) appends events;
enrichment cache keyed by ticket_id — no re-enrichment of seen ids.
RED until Day 2 — do not implement on Day 1."""
import pytest

pytestmark = pytest.mark.day2

from conftest import THIRD_DECLINE_ID, DECLINE_IDS, make_record

from src.watch import process_stream


def _stream(tickets, ids_in_order):
    by_id = {t["ticket_id"]: t for t in tickets}
    theme = lambda tid: "cards_online_declines" if tid in DECLINE_IDS else f"other_{tid}"
    return [make_record(by_id[tid], theme(tid)) for tid in ids_in_order]


def test_incident_declared_on_third_decline(tickets):
    events = []
    process_stream(_stream(tickets, ["TKT-2059", "TKT-2069", "TKT-2060"]), events.append)
    kinds = [e["event"] for e in events]
    assert kinds.count("INCIDENT_DECLARED") == 1
    declared = next(e for e in events if e["event"] == "INCIDENT_DECLARED")
    assert declared["trigger_ticket"] == THIRD_DECLINE_ID
    # declared strictly after the third TICKET_ARRIVED, never before
    assert kinds.index("INCIDENT_DECLARED") > kinds.index("TICKET_ARRIVED", 2)


def test_risk_ticket_pinned_on_arrival(tickets):
    events = []
    records = _stream(tickets, ["TKT-2079"])
    records[0]["risk_flags"] = ["ato", "access_control"]
    process_stream(records, events.append)
    assert any(e["event"] == "RISK_PINNED" and e["ticket_id"] == "TKT-2079" for e in events)


def test_seeded_history_is_silent_but_counts_toward_clusters(tickets):
    # replay starts at a cursor: pre-cursor history seeds the detector state
    # without emitting arrival events — then the FIRST streamed ticket that
    # completes a cluster triggers the declaration.
    events = []
    seed = _stream(tickets, ["TKT-2059", "TKT-2069"])
    live = _stream(tickets, ["TKT-2060"])
    process_stream(live, events.append, seed=seed)
    kinds = [e["event"] for e in events]
    assert kinds.count("TICKET_ARRIVED") == 1          # only the live ticket
    assert "INCIDENT_DECLARED" in kinds
    declared = next(e for e in events if e["event"] == "INCIDENT_DECLARED")
    assert declared["trigger_ticket"] == "TKT-2060"


def test_seen_tickets_are_not_reenriched(tickets):
    calls = []
    records = _stream(tickets, ["TKT-2059", "TKT-2059"])  # duplicate arrival
    process_stream(records, lambda e: None, enrich_fn=lambda r: calls.append(r["ticket_id"]) or {})
    assert calls == ["TKT-2059"]
