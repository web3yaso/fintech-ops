"""metrics.py compute layer (spec §4: ops-first — money and risk before
ticket hygiene). Pure functions over enriched + tickets; HTML is smoke-tested
for key content and self-containment."""
from datetime import datetime

from src.metrics import (deflection_candidates, detection_lag_hours,
                         generate_html, oldest_open_investigation_hours,
                         risk_exposure, segment_health, stuck_funds)


def _t(tid, customer, mrr=1000, status="open", res=None, csat=None):
    return {"ticket_id": tid, "customer_name": customer, "monthly_revenue_usd": mrr,
            "status": status, "resolution_time_hours": res, "csat_score": csat,
            "created_at": datetime(2026, 8, 10, 9, 0), "product": "Payments",
            "ticket_subject": "s", "ticket_body": "b", "customer_segment": "SMB",
            "country": "Canada"}


def _e(tid, segment="workflow", wf="payment_investigation", amount=None,
       flags=(), theme="th"):
    return {"ticket_id": tid, "segment": segment, "ops_workflow": wf,
            "theme": theme, "severity": 3, "risk_flags": list(flags),
            "amount_usd": amount, "summary": "s", "suggested_action": "a",
            "needs_human": False}


def test_stuck_funds_dedupes_followups_and_skips_resolved():
    by_id = {"T1": _t("T1", "Acme"), "T2": _t("T2", "Acme"),
             "T3": _t("T3", "Beta"), "T4": _t("T4", "Gama", status="resolved", res=5.0)}
    enriched = {"T1": _e("T1", amount=118000), "T2": _e("T2", amount=118000),  # follow-up, same wire
                "T3": _e("T3", amount=42000), "T4": _e("T4", amount=64000)}    # resolved: excluded
    assert stuck_funds(enriched, by_id) == 160000


def test_risk_exposure_counts_distinct_customers_with_open_security_flags():
    by_id = {"T1": _t("T1", "Acme", mrr=5000), "T2": _t("T2", "Acme", mrr=5000),
             "T3": _t("T3", "Beta", mrr=700),
             "T4": _t("T4", "Gama", mrr=9000, status="resolved", res=2.0)}
    enriched = {"T1": _e("T1", flags=["ato"]), "T2": _e("T2", flags=["fraud"]),
                "T3": _e("T3", flags=["churn_risk"]),      # not a security flag
                "T4": _e("T4", flags=["fraud"])}           # resolved: excluded
    assert risk_exposure(enriched, by_id) == 5000


def test_segment_health_averages_resolved_only():
    by_id = {"T1": _t("T1", "A", status="resolved", res=4.0, csat=5),
             "T2": _t("T2", "B", status="resolved", res=8.0, csat=3),
             "T3": _t("T3", "C")}  # open: excluded from resolution avg
    enriched = {"T1": _e("T1", segment="faq"), "T2": _e("T2", segment="faq"),
                "T3": _e("T3", segment="faq")}
    rows = segment_health(enriched, by_id)
    faq = next(r for r in rows if r["segment"] == "faq")
    assert faq["n"] == 3 and faq["avg_resolution_h"] == 6.0 and faq["avg_csat"] == 4.0


def test_deflection_candidates_ranked_by_volume_with_hours_saved():
    by_id = {f"T{i}": _t(f"T{i}", f"C{i}", status="resolved", res=float(h), csat=4)
             for i, h in enumerate([2, 4, 6, 10, 10])}
    enriched = {f"T{i}": _e(f"T{i}", segment="faq", wf="faq_selfserve",
                            theme="statement_download" if i < 3 else "card_limit")
                for i in range(5)}
    cands = deflection_candidates(enriched, by_id)
    assert cands[0]["theme"] == "statement_download"
    assert cands[0]["count"] == 3 and cands[0]["hours_saved"] == 12.0  # 3 x median 4h


def test_oldest_open_investigation_age():
    now = datetime(2026, 8, 13, 9, 0)
    by_id = {"T1": dict(_t("T1", "A"), created_at=datetime(2026, 8, 8, 9, 0)),   # 120h open
             "T2": dict(_t("T2", "B"), created_at=datetime(2026, 8, 12, 9, 0)),  # 24h open
             "T3": dict(_t("T3", "C", status="resolved", res=2.0),
                        created_at=datetime(2026, 8, 1, 9, 0))}                  # resolved: excluded
    enriched = {t: _e(t) for t in by_id}
    assert oldest_open_investigation_hours(enriched, by_id, now) == 120.0


def test_detection_lag_is_first_to_third_ticket():
    # burst threshold is 3 tickets: the lag from first report to declaration
    # is exactly first→third member creation time
    by_id = {f"T{i}": dict(_t(f"T{i}", f"C{i}"),
                           created_at=datetime(2026, 8, 4, 8 + i, 30))
             for i in range(4)}  # 08:30, 09:30, 10:30, 11:30
    cluster = {"member_ids": ["T3", "T0", "T2", "T1"]}  # unordered on purpose
    assert detection_lag_hours(cluster, by_id) == 2.0   # 08:30 → 10:30


def test_html_is_selfcontained_with_key_sections():
    by_id = {"T1": _t("T1", "Acme"), "T2": _t("T2", "Beta", status="resolved", res=3.0, csat=5)}
    enriched = {"T1": _e("T1", amount=42000, flags=["ato"]),
                "T2": _e("T2", segment="faq", wf="faq_selfserve", theme="faq_x")}
    clusters = {"incidents": [{"cluster_id": "INC-001", "kind": "incident",
                               "theme": "cards_online_declines", "member_ids": ["T1"],
                               "customers": ["Acme"], "avg_csat": 1.6,
                               "first_seen": "2026-08-04 08:30", "last_seen": "2026-08-07 00:27"}],
                "trends": [{"cluster_id": "TRD-001", "kind": "trend",
                            "theme": "fx_rate_complaints", "member_ids": ["T2"],
                            "customers": ["Beta"], "avg_csat": 1.67,
                            "first_seen": "2026-07-20 10:00", "last_seen": "2026-08-07 14:00"}]}
    actions = [{"ts": "2026-08-19T11:00:00", "actor": "liaison",
                "action": "owner_acked", "tickets": ["T1"], "artifact": "INC-001"}]
    events = [{"event": "INCIDENT_DECLARED", "cluster_id": "INC-001",
               "created_at": "2026-08-04 08:30:00"}]
    html = generate_html(enriched, by_id, clusters, week="2026-W34",
                         actions=actions, events=events)
    for needle in ["INC-001", "TRD-001", "Stuck inbound funds", "MRR exposed",
                   "prefers-color-scheme", "table", "2026-W34",
                   "owner_acked"]:                       # closure state on the card
        assert needle in html, needle
    assert "http://" not in html and "https://" not in html  # self-contained
