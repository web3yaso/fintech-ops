"""Trend detector: same theme, >=5 distinct customers over >=14 days,
avg CSAT (of scored tickets) <= 2.5. Plus the precedence rule: a theme that
qualifies as a trend absorbs its burst candidates (spec §2)."""
from datetime import datetime, timedelta

from conftest import FX_IDS

from src.clustering import cluster


def test_fx_trend_detected_with_full_membership(enriched_full):
    result = cluster(enriched_full)
    fx = [t for t in result.trends if t["theme"] == "fx_pricing_complaint"]
    assert len(fx) == 1
    assert set(fx[0]["member_ids"]) == FX_IDS


def test_high_csat_theme_is_not_a_trend(enriched_full):
    # vendor-payment FAQ: 7 tickets, 6 customers, 5-week span — but avg CSAT
    # 3.14 > 2.5. Volume alone must not create a trend.
    result = cluster(enriched_full)
    assert all(t["theme"] != "faq_vendor_payment" for t in result.trends)


def test_precedence_trend_absorbs_burst_candidates(enriched_full):
    # FX tail bunches up: Aug 1-5 holds two 72h windows with 3 tickets each.
    # Without precedence the burst pass would declare a mini-incident there.
    result = cluster(enriched_full)
    assert all(c["theme"] != "fx_pricing_complaint" for c in result.incidents)
    seen = {}
    for c in result.incidents + result.trends:
        for tid in c["member_ids"]:
            assert tid not in seen, f"{tid} in two clusters: {seen[tid]}, {c['theme']}"
            seen[tid] = c["theme"]


def test_trend_needs_five_distinct_customers():
    t0 = datetime(2026, 7, 1, 9, 0)
    records = [
        {"ticket_id": f"SYN-{i}", "created_at": t0 + timedelta(days=4 * i),
         "customer_name": f"C{i % 4}", "product": "FX", "theme": "syn_fx",
         "csat_score": 1.0}
        for i in range(6)  # 6 tickets, 20-day span, low CSAT — but 4 customers
    ]
    assert cluster(records).trends == []
