"""Priority score (spec §4):
priority = severity_weight[1,2,4,8] x (1 + log10(1 + MRR)) x age_factor(hours_open)
           + 50 if risk_flags else 0
Contract: src/scoring.py::priority_score(severity, mrr, hours_open, has_risk_flags)"""
import pytest

from src.scoring import priority_score


def test_risk_flag_adds_exactly_50():
    base = priority_score(3, 10_000, 24, has_risk_flags=False)
    flagged = priority_score(3, 10_000, 24, has_risk_flags=True)
    assert flagged - base == pytest.approx(50)


def test_monotonic_in_severity():
    scores = [priority_score(s, 5_000, 12, False) for s in (1, 2, 3, 4)]
    assert scores == sorted(scores) and len(set(scores)) == 4


def test_monotonic_in_mrr():
    assert priority_score(2, 50_000, 12, False) > priority_score(2, 500, 12, False)


def test_age_never_decreases_priority():
    assert priority_score(2, 5_000, 72, False) >= priority_score(2, 5_000, 1, False)


def test_flagged_low_mrr_outranks_unflagged_faq_of_highest_mrr():
    # The ATO ticket ("Quick question", $2.4k MRR customer) must outrank any
    # severity-1 FAQ even from the largest customer ($10.1k MRR).
    ato = priority_score(4, 2_400, 24, has_risk_flags=True)
    faq = priority_score(1, 10_100, 24, has_risk_flags=False)
    assert ato > faq
