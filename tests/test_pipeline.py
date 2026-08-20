"""Pipeline glue (spec §4): append-only enrichment cache (never re-spend on
a classified ticket) and queue assembly (risk tickets pinned to top).
Contract: src/pipeline.py::enrich_all / build_queue."""
import json
from datetime import datetime

from src.pipeline import build_queue, enrich_all

VALID_TEMPLATE = {
    "segment": "faq", "ops_workflow": "faq_selfserve", "theme": "faq_generic",
    "severity": 1, "risk_flags": [], "amount_usd": None,
    "summary": "s", "suggested_action": "a",
}


def _client_counting(calls):
    def client(prompt):
        tid = json.loads(prompt[prompt.rindex("{\"ticket_id\""):])["ticket_id"]
        calls.append(tid)
        return json.dumps(dict(VALID_TEMPLATE, ticket_id=tid))
    return client


def test_enrich_all_caches_across_runs(tickets, tmp_path):
    cache = tmp_path / "enriched.jsonl"
    subset = tickets[:5]
    calls = []
    first = enrich_all(subset, _client_counting(calls), cache_path=cache)
    assert sorted(calls) == sorted(t["ticket_id"] for t in subset)
    calls.clear()
    second = enrich_all(subset, _client_counting(calls), cache_path=cache)
    assert calls == []                      # nothing re-enriched
    assert second.keys() == first.keys()


def test_queue_sorted_and_risk_pinned(tickets, by_id):
    now = datetime(2026, 8, 13, 16, 0)
    enriched = {
        # low-MRR risk ticket vs high-MRR severity-3 incident ticket
        "TKT-2079": {"ticket_id": "TKT-2079", "segment": "workflow",
                     "ops_workflow": "fraud_ato", "theme": "ato_unknown_admin",
                     "severity": 4, "risk_flags": ["ato"], "amount_usd": None,
                     "summary": "s", "suggested_action": "a", "needs_human": False},
        "TKT-2063": {"ticket_id": "TKT-2063", "segment": "incident_candidate",
                     "ops_workflow": "card_ops", "theme": "cards_online_declines",
                     "severity": 3, "risk_flags": [], "amount_usd": None,
                     "summary": "s", "suggested_action": "a", "needs_human": False},
        "TKT-2001": {"ticket_id": "TKT-2001", "segment": "faq",
                     "ops_workflow": "faq_selfserve", "theme": "faq_user_permissions",
                     "severity": 1, "risk_flags": [], "amount_usd": None,
                     "summary": "s", "suggested_action": "a", "needs_human": False},
    }
    queue = build_queue(enriched, by_id, now=now)
    ids = [q["ticket_id"] for q in queue]
    assert ids[0] == "TKT-2079"             # risk pinned first
    assert ids.index("TKT-2063") < ids.index("TKT-2001")
    assert all("priority" in q and "explain" in q for q in queue)
    assert queue[0]["pinned"] is True and queue[-1]["pinned"] is False


def test_churn_risk_is_not_pinned_and_gets_no_offset(tickets, by_id):
    # churn matters through the trend escalation, not per-ticket pinning —
    # otherwise 11 FX tickets flood the top of the queue.
    now = datetime(2026, 8, 13, 16, 0)
    base = {"segment": "trend_candidate", "ops_workflow": "fx_pricing",
            "theme": "fx_pricing_complaint", "severity": 2, "amount_usd": None,
            "summary": "s", "suggested_action": "a", "needs_human": False}
    enriched = {
        "TKT-2055": dict(base, ticket_id="TKT-2055", risk_flags=["churn_risk"]),
        "TKT-2049": dict(base, ticket_id="TKT-2049", risk_flags=[]),
    }
    queue = build_queue(enriched, by_id, now=now)
    q55 = next(q for q in queue if q["ticket_id"] == "TKT-2055")
    q49 = next(q for q in queue if q["ticket_id"] == "TKT-2049")
    assert q55["pinned"] is False
    # same severity, no +50: any priority gap comes only from MRR/age factors
    assert abs(q55["priority"] - q49["priority"]) < 50
