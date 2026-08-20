"""Burst detector: same theme, tickets chained <=72h apart, >=3 tickets.
Contract under test: src/clustering.py::cluster(records) -> result with
.incidents / .trends, each cluster a dict with "theme" and "member_ids"."""
from datetime import datetime, timedelta

from conftest import DECLINE_IDS, WIRE_IDS, THIRD_DECLINE_ID, make_record

from src.clustering import cluster


def _decline_records(tickets, n):
    recs = sorted(
        (t for t in tickets if t["ticket_id"] in DECLINE_IDS),
        key=lambda t: t["created_at"],
    )[:n]
    return [make_record(t, "cards_online_declines") for t in recs]


def test_burst_fires_on_third_ticket_in_window(tickets):
    records = _decline_records(tickets, 3)
    assert records[-1]["ticket_id"] == THIRD_DECLINE_ID
    result = cluster(records)
    assert len(result.incidents) == 1
    assert set(result.incidents[0]["member_ids"]) == {r["ticket_id"] for r in records}


def test_no_burst_below_three_tickets(tickets):
    result = cluster(_decline_records(tickets, 2))
    assert result.incidents == []


def test_gap_over_72h_breaks_chain():
    t0 = datetime(2026, 8, 1, 9, 0)
    records = [
        {"ticket_id": f"SYN-{i}", "created_at": t0 + timedelta(hours=80 * i),
         "customer_name": f"C{i}", "product": "Cards", "theme": "syn_theme",
         "csat_score": 1.0}
        for i in range(3)
    ]
    assert cluster(records).incidents == []


def test_faq_theme_never_bursts(enriched_full):
    # "statement download" FAQ: 6 verbatim repeats, 4 inside one 72h window.
    # Volume-bunching alone must not declare an incident for faq records —
    # and a CSAT gate can't be the fix, because live-arriving tickets have
    # no CSAT yet. The segment field is the gate.
    result = cluster(enriched_full)
    assert all(c["theme"] != "faq_statement_download" for c in result.incidents)


def test_full_dataset_yields_exactly_two_incidents(enriched_full):
    result = cluster(enriched_full)
    assert len(result.incidents) == 2
    memberships = {frozenset(c["member_ids"]) for c in result.incidents}
    assert frozenset(DECLINE_IDS) in memberships
    assert frozenset(WIRE_IDS) in memberships
